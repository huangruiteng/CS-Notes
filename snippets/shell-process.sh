
*** 绑核

taskset -c 0-15,32-47

*** kill

ps aux | grep 'xxx' | grep -v grep | awk '{print $2}' | xargs kill -9