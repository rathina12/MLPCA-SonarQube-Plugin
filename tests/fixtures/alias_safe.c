#include <stdlib.h>
void alias_safe(void) {
    int *p = (int*)malloc(10);
    int *q = p;
    free(q);
}
