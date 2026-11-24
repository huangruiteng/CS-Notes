#ifndef __vector_header_h__
#define __vector_header_h__

#define VECTOR_SIZE (100)

typedef struct __vector {
    pthread_mutex_t lock;
    int values[VECTOR_SIZE];
} vector_t;


#endif // __vector_header_h__

