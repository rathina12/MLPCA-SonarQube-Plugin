#include <stdlib.h>
void release(int *p) { free(p); }
void interproc(void) {
    int *p = (int*)malloc(10);
    release(p);
}
