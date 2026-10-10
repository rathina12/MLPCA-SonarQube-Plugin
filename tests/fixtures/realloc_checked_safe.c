#include <stdlib.h>
void example(void) {
  int *p = malloc(16);
  void *q = realloc(p, 32);
  if (q) { free(q); } else { free(p); }
}
