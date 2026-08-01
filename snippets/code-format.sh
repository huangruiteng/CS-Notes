
yapf --in-place --recursive --style="{based_on_style:google,indent_width:2}" ./


clang-format -style=Google -dump-config > ~/.clang-format