#include <stdlib.h>
void early(int c) {
    int *p = (int*)malloc(10);
    if (c) return;
    free(p);
}
