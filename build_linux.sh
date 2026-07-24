gcc -O2 -s -static -o zombie_linux zombie_payload.c -lpthread -lcurl
upx --ultra-brute zombie_linux -o zombie_linux_obf