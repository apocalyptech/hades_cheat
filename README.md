Hades Cheat Injector
--------------------

This is a little cheat injector I made for myself, for the excellent
game [Hades, from Supergiant Games](https://www.supergiantgames.com/games/hades/).
It's a roguelike which relies on running through its levels many
times to advance the game's multiple storylines and collect/enhance all
the various abilities and such.  It's a testament to the game that it
hooked me in despite being a roguelike, a genre that I typically just
don't have the patience for.

Nevertheless, I eventually got tired of having to progress "normally,"
and even the game's built-in "God Mode" was slow enough to develop that
I decided to start cheating more overtly.  At first I was mostly just
increasing the rate at which items were acquired, but eventually I worked
my way up to full-on cheating (buffing weapon damage, etc).

Basically all of the game's balancing and functionality is exposed via
text files in the game's directories, and these can be edited at will.
They're a mix of [LUA scripts](https://www.lua.org/) and
[Simplified JSON](http://bitsquid.blogspot.com/2009/10/simplified-json-notation.html).
I edited them by hand for awhile but eventually got to wanting a more
powerful way of making tweaks -- for instance, having a single scaling
parameter for weapon damage which I could set once, rather than having
to update dozens of values strewn between multiple files.

So, this little script was written.  It takes a collection of "templates,"
which are just copies of the stock game files with a custom macro specification
added in.  The script loops through the file looking for those macro tags,
making changes where appropriate, and writes out the updated version to the
game's directory.  The actual tweaks are all specified in code, so you'll have
to edit the script to make any changes you want.  It should be pretty trivial
to add in any new tweaks as well: add in whatever macro tags you feel are
appropriate, and then add them to the `changes` dictionary near the bottom of
the script.

Currently the script makes the following changes:

* Weapon damage scaled by 1.3x
* Darkness drop quantity buffed by a *lot*
* Gem drop quantity buffed by a bit less, but still a lot
* Money drops increased pretty significantly
* Many shop items (both Well of Charon and the official Shop) are cheaper
  * Styx shop Diamonds and Titan Blood are discounted even more.
* Health buffs increased slightly
* Nectar/Ambrosia/Keys/Diamonds/Titan Blood have 10x per drop, instead of 1x.
* Every possible fishing point will be active
* Fishing is easier (no fake-outs, "perfect" window is doubled)
* God Mode is improved by 20%
* Keepsakes level up every 2 encounters (instead of 25 + 50)
* Mid-level Charon shops will always have shoplifting opportunity
* Infernal Gates cost 4/8/12 (instead of 5/10/15), and will spawn
  much more frequently
* Thanatos can spawn starting at the very beginning of each zone.

Note that none of that is necessarily exhaustive -- I wouldn't be surprised
if there are some unbuffed damage values, and various shop items have not
had their prices updated, for instance.

Game Compatibility
------------------

The files in the `templates` dir were originally copied from game version
v1.38290, which was the current version around mid-to-late May 2022.  If the
game's been updated since then, it's entirely possible that some of those files
may have been updated.  In that case, the changes would need to be merged back
in to the templates for the script to remain compatible.

Likewise, if you have any ["real" Hades mods](https://www.nexusmods.com/hades)
installed, those mods may have overwritten some of the files that we edit, so
this wouldn't be compatible with those unless the mod changes were merged into
these templates.

Installation
------------

This script requires Python 3.10+.  There's no real installation --
just check it out from git, make sure you have Python 3.10+ installed,
make sure the `chardet` Python library is installed, and then run it
from the commandline.

The script was developed/tested on Linux, but should probably work
just fine on any platform which can run Python.

### Dependencies

The project makes use of the following:
 - `chardet`: https://pypi.org/project/chardet/

Either use `pip install chardet` to install it, or
`pip install -r requirements.txt`.  (It might also be available in your
distro's package manager, on Linux systems.)

Usage
-----

Running the script with `-h` or `--help` will show you the syntax:

    usage: hades_cheat.py [-h] [-t TEMPLATE_DIR] [-d DEST_DIR] [-l]

    Hades Cheat Injector

    options:
      -h, --help            show this help message and exit
      -t TEMPLATE_DIR, --template-dir TEMPLATE_DIR
                            Directory in which to find templates (default:
                            templates)
      -d DEST_DIR, --dest-dir DEST_DIR
                            Directory in which to write our modified files
                            (default: /games/Steam/steamapps/common/Hades/Content)
      -l, --list-changes    Instead of processing, show the macro changes we'd
                            apply (default: False)

The default `templates` dir for the templates is included in this
repo; you'll almost certainly have to specify the game's `Content` directory
location yourself, though.  Running it on my system yields the following:

    $ ./hades_cheat.py
    Processing: Game/Projectiles/PlayerProjectiles.sjson
    Processing: Scripts/RoomDataSurface.lua
    Processing: Scripts/TraitData.lua
    Processing: Scripts/HeroData.lua
    Processing: Scripts/RoomDataStyx.lua
    Processing: Scripts/ConsumableData.lua
    Processing: Scripts/RoomDataAsphodel.lua
    Processing: Scripts/RoomDataTartarus.lua
    Processing: Scripts/FishingData.lua
    Processing: Scripts/StoreData.lua
    Processing: Scripts/RoomDataSecrets.lua
    Processing: Scripts/RoomDataElysium.lua

Using `-l` or `--list-changes` will have the script output the changes that
it will make, listing out the macro tag and then the action that gets
applied.  Here's the default set:

    $ ./hades_cheat.py -l
                   damage_scale: Scale by 1.3
             damage_scale_float: Scale by 1.300000 as a float
                    base_health: Hardcoded to: 100 (disabled, using defaults)
            well_darkness_scale: Scale by 4
       well_darkness_cost_scale: Scale by 0.250000 as a float
                 well_gem_scale: Scale by 6
            well_gem_cost_scale: Scale by 0.166667 as a float
                shop_cost_scale: Scale by 0.5
          super_shop_cost_scale: Scale by 0.25
                     health_qty: Hardcoded to: 20
                  maxhealth_qty: Hardcoded to: 30
                      money_qty: Hardcoded to: 400
                money_minor_qty: Hardcoded to: 80
           gems_extra_money_qty: Hardcoded to: 60
            darkness_reward_qty: Hardcoded to: 500
              shop_darkness_qty: Hardcoded to: 200
            boss_darkness_scale: Scale by 10
               various_gems_qty: Hardcoded to: 200
                     nectar_qty: Hardcoded to: 10
                   ambrosia_qty: Hardcoded to: 10
                       keys_qty: Hardcoded to: 10
                   diamonds_qty: Hardcoded to: 10
                titan_blood_qty: Hardcoded to: 10
              fishing_max_fakes: Hardcoded to: 0
       fishing_perfect_interval: Hardcoded to: 0.64
                 fishing_chance: Fishing Minimum Chance: 100%, Space Between Rooms: 1
             fishing_room_space: Fishing Minimum Chance: 100%, Space Between Rooms: 1
             godmode_base_scale: God Mode from 60% -> 0%, with 30 steps
              godmode_per_death: God Mode from 60% -> 0%, with 30 steps
              godmode_death_cap: God Mode from 60% -> 0%, with 30 steps
           keepsake_activations: Hardcoded to: 2, 2
         charon_shoplift_chance: Hardcoded to: 1
    infernal_gate_cost_tartarus: Hardcoded to: 4
    infernal_gate_cost_asphodel: Hardcoded to: 8
     infernal_gate_cost_elysium: Hardcoded to: 12
           infernal_gate_chance: Hardcoded to: 0.5
       infernal_gate_room_space: Hardcoded to: 2
       thanatos_min_spawn_depth: Hardcoded to: 1

There are also a couple of shell scripts in the directory which can kick
off some diffs, just for an easy spot-check of what the util did.  These are
just intended for Linux systems, but can probably be run in
[WSL](https://docs.microsoft.com/en-us/windows/wsl/install) or on OSX, too.
The scripts require having copied the game's stock `Content` directory contents
into a `Content-orig` directory, though you can of course edit the scripts to
change that.  The scripts also have a hardcoded path to the game's live `Content`
directory, so that will almost certainly need changing on your system as well.

`diff-templates.sh` shows what's changed between the stock game files and the
templates.  `diff-live.sh` shows what's changed between the stock game files
and the edited files generated by the script.

Templates / Macros
------------------

The macro syntax used in the templates is an entirely custom format, but it's
easy enough.  For instance, around line 156 in `Scripts/ConsumableData.lua`,
the start of the `GiftDrop` stanza (which deals with Nectar drops) looks like
this once the macros have been added:

    GiftDrop =
    {
        InheritFrom = { "BaseConsumable" },
        RequiredBiomes = { "Elysium", "Styx" },
        Cost = @shop_cost_scale|200@,
        AddResources =
        {
            GiftPoints = @nectar_qty|1@,
        },
        ....

As you can see, it's enclosed by `@` symbols, with a pipe (`|`) inbetween the
macro name and the original (default) value.  Inside the `changes` dict in
the script itself, you'll see the following lines:

    'shop_cost_scale': ActionScaleInt(0.5),
    'nectar_qty': ActionHardcode(10),

So when the script encounters a `shop_cost_scale` tag in the template, it'll
take the default value (`200` in this case), multiply it by `0.5`, and write
it back out as an integer.  When it encounters `nectar_qty`, it'll completely
replace the value with `10`, ignoring whatever was in the default value.  So
that stanza, once written out to the game directory, would look like:

    GiftDrop =
    {
        InheritFrom = { "BaseConsumable" },
        RequiredBiomes = { "Elysium", "Styx" },
        Cost = 100,
        AddResources =
        {
            GiftPoints = 10,
        },
        ....

Note that the script currently only supports having a single macro tag per
line, since I didn't need more than one and didn't feel like trying to support
that.

LICENSE
-------

Hades Cheat Injector code is licensed under the
[New/Modified (3-Clause) BSD License](https://opensource.org/licenses/BSD-3-Clause).
A copy is also found in [COPYING.txt](COPYING.txt).

The templates found in the `templates` directory have been copied from the
Hades game data itself, and AFAIK would be copyright by
[Supergiant Games](https://www.supergiantgames.com/).  Those are *not*
covered under the same license as my code, and honestly I'm not even
sure what their redistribution terms are like.  I assume since the Hades
area of Nexus Mods is tolerated, Supergiant doesn't mind this sort of
redistribution -- perhaps it's covered by Fair Use?

Changelog
---------

**2022-06-01**:
 * Added Thanatos spawn tweaks

**2022-05-28**:
 * Added in Infernal Gate tweaks

**2022-05-27**:
 * Added in improved elite/hard room rewards for gems/darkness/keys.

**2022-05-26**:
 * Added in damage scaling for the various Daedalus Hammer upgrades which
   had absolute damage values; missed those previously.

**2022-05-25**:
 * Initial release
 * Added Charon shoplift chance

