# Shows the changes we've made, compared to the stock game files
# (requires having copied the stock game files to `Content-orig`)
diff -ru --color=always Content-orig /games/Steam/steamapps/common/Hades/Content | grep -vE '^Only in' | less -Ri
