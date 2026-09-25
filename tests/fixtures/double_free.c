#include <stdlib.h>
void df(void) {
    int *p = (int*)malloc(10);
    free(p);
    free(p);
}
