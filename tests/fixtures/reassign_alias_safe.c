#include <stdlib.h>
void example(void) {
  int *p = malloc(sizeof(int));
  int *q = p;
  p = 0;
  free(q);
}
