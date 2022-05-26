#!/usr/bin/env python3
# vim: set expandtab tabstop=4 shiftwidth=4:

# Hades Cheat Injector
# Copyright (C) 2022 CJ Kucera 
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#     * Redistributions of source code must retain the above copyright
#       notice, this list of conditions and the following disclaimer.
#     * Redistributions in binary form must reproduce the above copyright
#       notice, this list of conditions and the following disclaimer in the
#       documentation and/or other materials provided with the distribution.
#     * Neither the name of the development team nor the
#       names of its contributors may be used to endorse or promote products
#       derived from this software without specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL CJ KUCERA BE LIABLE FOR ANY
# DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

import os
import re
import io
import sys
import math
import codecs
import chardet
import argparse

# We use the `match` statement introduced in 3.10
if sys.version_info < (3, 10):
    raise RuntimeError('This utility requires at least Python 3.10')

class Action:
    """
    Base Action class to process our templates; unusuable on
    its own.
    """

    def __init__(self, use_default=False):
        """
        Setting `use_default = True` will cause the action to
        always just use the default -- this could be useful if
        you want to stop modifying some attributes but retain the
        config in the file here.
        """
        self.use_default = use_default

    def desc(self):
        if self.use_default:
            return '{} (disabled, using defaults)'.format(self._desc())
        else:
            return self._desc()

    def _desc(self):
        raise NotImplementedError('Implement this!')

    def _process(self, name, default):
        raise NotImplementedError('Implement this!')

    def process(self, name, default):
        if self.use_default:
            return default
        else:
            return self._process(name, default)

class ActionDefault(Action):
    """
    An Action which always returns the default value
    """

    def __init__(self):
        super().__init__(True)

    def desc(self):
        """
        Overriding the default behavior here
        """
        return 'Always use default'

    def _process(self, name, default):
        """
        A bit silly to implement this, but I suppose this way it'll
        still default even if someone sets `use_default = True`
        """
        return default

class ActionScaleInt(Action):
    """
    An action which scales by the specified factor and always returns
    an integer (rounding if needed: >=x.5 will round up, <x.5 will
    round down).
    """

    def __init__(self, scale, inverse=False, use_default=False):
        """
        Specify `inverse = True` to scale down by the given factor
        rather than up.
        """
        super().__init__(use_default)
        self.inverse = inverse
        if inverse:
            self.scale = 1/scale
        else:
            self.scale = scale

    def _desc(self):
        return f'Scale by {self.scale}'

    def _process(self, name, default):
        new_val = float(default) * self.scale
        # I like this better than the `round()` builtin because it handles .5
        # how I'd like.
        return math.floor(new_val + 0.5)

class ActionScaleFloat(ActionScaleInt):
    """
    An action which scales by the specified factor and returns a
    float.
    """

    def __init__(self, scale, inverse=False, precision=6, use_default=False):
        """
        `inverse` is the same as in ActionScaleInt.  Specify `precision` to
        determine how many decimal places to round to.
        """
        super().__init__(scale, inverse=inverse, use_default=use_default)
        self.precision = precision

    def _desc(self):
        fstring = f'Scale by {{:0.{self.precision}f}} as a float'
        return fstring.format(self.scale)

    def _process(self, name, default):
        new_val = float(default) * self.scale
        return round(new_val, self.precision)

class ActionHardcode(Action):
    """
    An action which hardcodes to the specified value
    """

    def __init__(self, val, use_default=False):
        """
        Pass in `val` for the value to hardcode.
        """
        super().__init__(use_default)
        self.val = val

    def _desc(self):
        return f'Hardcoded to: {self.val}'

    def _process(self, name, default):
        return self.val

class ActionGodMode(Action):
    """
    Action to handle our God Mode config.  Create one instance of
    this and bind it to multiple macro names.  Handles the following:
        godmode_base_scale
        godmode_per_death
        godmode_death_cap
    """

    def __init__(self, start_pct, end_pct, steps=30, use_default=False):
        """
        `start_pct` is the base damage scaling, and `end_pct` is the
        final damage scaling after dying `steps` times.  The effective
        defaults are 0.8 for `start_pct` and 0.2 for `end_pct`, though
        `end_pct` doesn't actually show up in the game's scripts at all.
        """
        super().__init__(use_default)
        self.start_pct = start_pct
        self.end_pct = end_pct
        self.steps = steps
        self.step = (self.end_pct-self.start_pct)/self.steps

    def _desc(self):
        return 'God Mode from {}% -> {}%, with {} steps'.format(
                int(self.start_pct*100),
                int(self.end_pct*100),
                self.steps,
                )

    def _process(self, name, default):
        match name:
            case 'godmode_base_scale':
                return self.start_pct
            case 'godmode_per_death':
                return round(self.step, 6)
            case 'godmode_death_cap':
                return self.steps
            case _:
                raise RuntimeError(f'Unknown GodMode macro name: {name}')

class ActionFishingChance(Action):
    """
    Action to handle the chances of having a fishing point spawn.  This
    takes the default values into to choose the "best" values, so it won't
    ever make any chances *worse* than the defaults.

    For instance, if you set the chance to 0.2 (20%), the chances for
    Tartarus (0.25) and Styx (0.30) will remain better, but the other
    areas will be improved.  Or if you change the minimum rooms to
    5, the three which already had better values will remain unchanged:
    Styx, Hades's spot, and Greece.

    You can create a single instance of this and assign it to more
    than one macro name.  The two that it supports are:
        fishing_chance
        fishing_room_space
    """

    def __init__(self, min_chance, min_rooms, use_default=False):
        """
        `min_chance` - the "minimum" fishing spot chance to set, though
            "minimum" here is a kind of a terrible term to use, since
            1.0 would beat out 0.1.
        `min_rooms` - The minimum number of rooms since the previous
            fishing spot, before another can spawn (`1` will make them
            always available)
        """
        super().__init__(use_default)
        self.min_chance = min_chance
        self.min_rooms = min_rooms

    def _desc(self):
        return 'Fishing Minimum Chance: {}%, Space Between Rooms: {}'.format(
                int(self.min_chance*100),
                self.min_rooms,
                )

    def _process(self, name, default):
        match name:
            case 'fishing_chance':
                return max(float(default), self.min_chance)
            case 'fishing_room_space':
                return min(int(default), self.min_rooms)
            case _:
                raise RuntimeError(f'Unknown Fishing macro name: {name}')

class TextProcessor:
    """
    ><

    So I want to recreate files as identically as possible.  This is a
    bit stupid of me given the various problems here -- Hades the game
    doesn't seem to actually care about a lot of this.  But I want my
    diffs to be as trivial as possible, so eh.  The problems:

        1. Newlines.  This should be easy, given Python's `newline`
           arg to `open()` but in practice I keep finding edge cases
           which result in messy diffs.  So I'm just handling it
           with a binary output file.  Fuck it.
        2. BOM.  The UTF-8-encoded files include a BOM.  `chardet`
           will detect it as such, but we can't just take its `encoding`
           value and encode each string, because each line would
           have a BOM marker.  Also it turns out that the first
           string read from the file (even in text mode!) includes
           the BOM, so we could end up with a double-BOM.  wtf.
        3. End-of-file newlines.  Mostly they're not present, but
           sometimes they are, and reading the files in text mode
           seems to obfuscate it.  Whatever, we're just not putting
           any in.  Currently this results in just one 'messy' diff.

    So whatever, we're being stupid about all this.  Use `chardet` to
    detect the encoding, and then only support a hardcoded few, handling
    the encoding and newline stuff sort-of manually.  We only support the
    two file encodings I've seen in the Hades data so far.  Meh.
    """

    def __init__(self, filename_orig, filename_new):
        self.filename_orig = filename_orig
        self.filename_new = filename_new
        self.written_line = False

        # Grab encoding
        with open(self.filename_orig, 'rb') as df:
            results = chardet.detect(df.read(1024))
            if results['confidence'] < 0.9:
                raise RuntimeError(f'Character detection not confident enough for {self.filename_orig}: {results}')
            self.orig_encoding = results['encoding']

        # Process encoding
        match self.orig_encoding:
            case 'UTF-8-SIG':
                self.encoding = 'utf-8'
                self.bom = codecs.BOM_UTF8
            case 'ascii':
                self.encoding = 'ascii'
                self.bom = None
            case _:
                raise RuntimeError(f'Unknown encoding in {self.filename_orig}: {self.orig_encoding}')

        # Read in the file data.  Inefficient!
        with open(self.filename_orig) as df:
            # Note that the universal-newline handling means that our line ending will
            # always be the single \n char.
            df.readline()
            if df.newlines is None:
                raise RuntimeError(f'Unknown line endings for {self.filename_orig}')
            self.newline = df.newlines.encode(self.encoding)
            df.seek(0)
            self.data = []
            first = True
            for line in df:
                if first:
                    first = False
                    if self.bom is not None:
                        self.data.append(line[len(self.bom.decode(self.encoding)):-1])
                    else:
                        self.data.append(line[:-1])
                else:
                    self.data.append(line[:-1])
        self.odf = None

    def __enter__(self):
        """
        Support/require opening in a `with` clause
        """
        self.odf = open(self.filename_new, 'wb')
        if self.bom is not None:
            self.odf.write(self.bom)
        return self

    def __exit__(self, exit_type, value, traceback):
        """
        Exiting from a `with` clause
        """
        self.odf.close()

    def __iter__(self):
        """
        Iterate over the original file lines
        """
        return iter(self.data)

    def write(self, text):
        """
        Write out a single line of text
        """
        if self.written_line:
            self.odf.write(self.newline)
        encoded = text.encode(self.encoding)
        self.odf.write(text.encode(self.encoding))
        self.written_line = True

class App:
    """
    Given a collection of templates, a "live" directory to write to, and a
    set of changes, process them!
    """

    macro_re = re.compile('^(?P<start>.*)@(?P<name>[a-z_]+)\|(?P<default>.*?)@(?P<end>.*)$')

    def __init__(self, template_dir, live_dir, changes):
        self.template_dir = template_dir
        self.live_dir = live_dir
        self.changes = changes
        self.default_action = ActionDefault()

    def process_files(self):
        """
        Process all files in our template dir
        """
        for dirpath, _, filenames in os.walk(self.template_dir):
            for filename in filenames:
                self.process_file(os.path.join(dirpath, filename)[len(self.template_dir)+1:])

    def process_file(self, filename):
        """
        Process the specified file -- should be the "base" path+filename
        which can be appended to either the template dir or the "live"
        dir.
        """

        print(f'Processing: {filename}')

        # Figure out paths and make sure we can write to the live dir.
        filename_template = os.path.join(self.template_dir, filename)
        filename_live = os.path.join(self.live_dir, filename)
        dirname_live = os.path.dirname(filename_live)
        if not os.path.exists(dirname_live):
            os.makedirs(dirname_live, exist_ok=True)

        # Loop through and look for our macros
        with TextProcessor(filename_template, filename_live) as tp:
            for line in tp:
                if match := self.macro_re.match(line):
                    start = match.group('start')
                    name = match.group('name')
                    default = match.group('default')
                    end = match.group('end')
                    if name in self.changes:
                        action = self.changes[name]
                    else:
                        print(f' - WARNING: Change key not found, using default: {name}')
                        action = self.default_action
                    tp.write('{}{}{}'.format(
                        start,
                        action.process(name, default),
                        end,
                        ))
                else:
                    tp.write(line)

def main():

    # Defaults: 0.8, 0.6
    godmode = ActionGodMode(0.6, 0)

    # Defaults:
    # Level                 Chance   Min Rooms Inbetween
    # -----                 ------   -------------------
    # Tartarus (first room) 0.1      10
    # Tartarus              0.25     10
    # Asphodel              0.1      10
    # Elysium               0.1      10
    # Chaos                 0.07     5
    # Styx                  0.30     1
    # Hades                 0.2      1
    # Greece                0.2      2
    fishing = ActionFishingChance(min_chance=1, min_rooms=1)

    # Change dict
    changes = {

            ###
            ### Direct Buffs
            ###

            # Scale up various weapon damage
            'damage_scale': ActionScaleInt(1.3),
            'damage_scale_float': ActionScaleFloat(1.3),

            # Health - default: 50
            'base_health': ActionHardcode(100, use_default=True),

            ###
            ### Commerce scaling!
            ###

            # Darkness/Gem cost at Well of Charon; prices are per-item and quantity is randomized
            'well_darkness_scale': ActionScaleInt(4),
            'well_darkness_cost_scale': ActionScaleFloat(4, inverse=True),
            'well_gem_scale': ActionScaleInt(6),
            'well_gem_cost_scale': ActionScaleFloat(6, inverse=True),

            # Shop cost ("super" is Diamonds and Titan Blood)
            'shop_cost_scale': ActionScaleInt(0.5),
            'super_shop_cost_scale': ActionScaleInt(0.25),

            ###
            ### Quantity overrides (tends to affect both shops + drops)
            ###

            # Health - default: 10
            'health_qty': ActionHardcode(20),
            # Max Health - default: 25
            'maxhealth_qty': ActionHardcode(30),

            # Money Drops - default: (various)
            'money_qty': ActionHardcode(400),
            # Minor Money Drops - default: 30
            'money_minor_qty': ActionHardcode(80),
            # Extra money with gems drops (depending on upgrades) - default: 20
            'gems_extra_money_qty': ActionHardcode(60),

            # Darkness (room reward) - default: 10
            'darkness_reward_qty': ActionHardcode(500),
            # Darkness (Charon's Shop) - default: 25
            'shop_darkness_qty': ActionHardcode(200),
            # Darkness - Boss reward scale - defaults: 50, 100, 150, 250
            'boss_darkness_scale': ActionScaleInt(10),

            # Gems (various sources) - default: 20 (Charon's shop), 5 (room rewards)
            'various_gems_qty': ActionHardcode(200),

            # Nectar - default: 1
            'nectar_qty': ActionHardcode(10),
            # Ambrosia - default: 1
            'ambrosia_qty': ActionHardcode(10),
            # Keys - default: 1
            'keys_qty': ActionHardcode(10),
            # Diamonds - default: 1
            'diamonds_qty': ActionHardcode(10),
            # Titan Blood - default: 1
            'titan_blood_qty': ActionHardcode(10),

            ###
            ### Fishing
            ###

            # Default: 3
            'fishing_max_fakes': ActionHardcode(0),
            # Default: 0.34
            'fishing_perfect_interval': ActionHardcode(0.64),

            # Defaults noted above
            'fishing_chance': fishing,
            'fishing_room_space': fishing,

            ###
            ### God Mode
            ###

            # Defaults noted above
            'godmode_base_scale': godmode,
            'godmode_per_death': godmode,
            'godmode_death_cap': godmode,

            ###
            ### Keepsakes
            ### (a bit hokey; our regex doesn't support more than one value per line)
            ###

            # Default: '25, 50'
            'keepsake_activations': ActionHardcode('2, 2'),

            ###
            ### Charon shoplift opportunity chance
            ###

            # Default: 0.22
            'charon_shoplift_chance': ActionHardcode(1),

            }

    # Eh, fine, support some args.
    parser = argparse.ArgumentParser(
            description='Hades Cheat Injector',
            formatter_class=argparse.ArgumentDefaultsHelpFormatter,
            )

    parser.add_argument('-t', '--template-dir',
            type=str,
            default='templates',
            help='Directory in which to find templates',
            )

    parser.add_argument('-d', '--dest-dir',
            type=str,
            default='/games/Steam/steamapps/common/Hades/Content',
            help='Directory in which to write our modified files',
            )

    parser.add_argument('-l', '--list-changes',
            action='store_true',
            help="Instead of processing, show the macro changes we'd apply",
            )

    args = parser.parse_args()

    # Run!
    if args.list_changes:
        label_max = max([len(k) for k in changes.keys()])
        fstring = f'{{:>{label_max}}}: {{}}'
        for label, change in changes.items():
            print(fstring.format(label, change.desc()))
    else:
        app = App(
                template_dir=args.template_dir,
                live_dir=args.dest_dir,
                changes=changes,
                )
        app.process_files()

if __name__ == '__main__':
    main()

