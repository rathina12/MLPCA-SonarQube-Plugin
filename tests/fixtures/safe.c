#include <stdlib.h>
void safe(void) {
    int *p = (int*)malloc(sizeof(int));
    free(p);
}
