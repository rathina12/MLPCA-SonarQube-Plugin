#include <stdlib.h>

void leak_on_error(int error) {
    char *buffer = (char *)malloc(256);
    if (error) {
        return;
    }
    free(buffer);
}

void safe_alias(void) {
    int *p = (int *)malloc(sizeof(int));
    int *q = p;
    free(q);
}
