#include <stdlib.h>

void grow_buffer(void) {
    char *buffer = (char *)malloc(16);
    if (!buffer) return;

    buffer = (char *)realloc(buffer, 32);
    free(buffer);
}
