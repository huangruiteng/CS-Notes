*** intro

__threadfence_block <-> __syncthreads
__threadfence
__threadfence_system

Declare shared variables as volatile
to make writes visible to other threads (prevents compiler from removing “redundant” read/writes)


*** atomicCAS

Use case: perform an arbitrary associative and commutative operation
atomically on a single variable

atomicCAS(p, old, new) does atomically
- if *p == old then assign *p←new, return old
- else return *p
_
_shared__ unsigned int data;
unsigned int old = data; // Read once
unsigned int assumed;
do {
	assumed = old;
	newval = f(old, x); // Compute
	old = atomicCAS(&data, old, newval); // Try to replace
} while(assumed != old); // If failed, retry
