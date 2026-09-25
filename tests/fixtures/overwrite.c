#include <stdlib.h>
void overwrite(void) {
    int *p = (int*)malloc(10);
    p = (int*)malloc(20);
    free(p);
}
