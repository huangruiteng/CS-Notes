#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "mythreads.h"

#include "main-header.h"
#include "vector-header.h"

// taken from https://en.wikipedia.org/wiki/Fetch-and-add
int fetch_and_add(int * variable, int value) {
    asm volatile("lock; xaddl %%eax, %2;"
		 :"=a" (value)                  
		 :"a" (value), "m" (*variable)  
		 :"memory");
    return value;
}

void vector_add(vector_t *v_dst, vector_t *v_src) {
    int i;
    for (i = 0; i < VECTOR_SIZE; i++) {
	fetch_and_add(&v_dst->values[i], v_src->values[i]);
    }
}

void fini() {}


#include "main-common.c"

