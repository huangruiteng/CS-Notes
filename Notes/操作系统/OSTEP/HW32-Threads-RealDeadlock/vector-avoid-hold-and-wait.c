#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include <unistd.h>

#include "mythreads.h"

#include "main-header.h"
#include "vector-header.h"

// use this to make lock acquisition ATOMIC
pthread_mutex_t global = PTHREAD_MUTEX_INITIALIZER; 

void vector_add(vector_t *v_dst, vector_t *v_src) {
    // put GLOBAL lock around all lock acquisition...
    Pthread_mutex_lock(&global);
    Pthread_mutex_lock(&v_dst->lock);
    Pthread_mutex_lock(&v_src->lock);
    Pthread_mutex_unlock(&global);
    int i;
    for (i = 0; i < VECTOR_SIZE; i++) {
	v_dst->values[i] = v_dst->values[i] + v_src->values[i];
    }
    Pthread_mutex_unlock(&v_dst->lock);
    Pthread_mutex_unlock(&v_src->lock);
}

void fini() {}

#include "main-common.c"

