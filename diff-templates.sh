# Shows a diff of our templates to the stock game files
# (requires having copied the stock game files to `Content-orig`)
diff -ru --color=always Content-orig templates | grep -vE '^Only in' | less -Ri
