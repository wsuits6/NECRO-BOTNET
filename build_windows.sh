x86_64-w64-mingw32-gcc -O2 -s -static -o zombie.exe zombie_payload.c -lws2_32 -lwininet -lpthread
upx --ultra-brute zombie.exe -o zombie_obf.exe