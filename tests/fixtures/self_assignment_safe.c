#include <stdlib.h>
void example(void) {
  int *p = malloc(sizeof(int));
  p = p;
  free(p);
}
