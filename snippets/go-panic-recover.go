package main

import (
	"context"
	"fmt"
	"runtime/debug"
	"sync"
)

/*
 * 笔记：Go Panic 安全执行模式
 *
 * 1. 背景：
 *    在 Go 中，如果一个 Goroutine 发生 panic 且没有被 recover，会导致整个程序（进程）崩溃。
 *    对于服务端程序（如 Web Server、RPC Server），我们不希望因为一个请求的处理异常导致整个服务挂掉。
 *    因此，通常需要一种机制来“安全地”执行代码，将 panic 转化为 error 处理。
 *
 * 2. 代码解析：AsyncExecutePanicToError
 *    该函数封装了“启动 Goroutine -> 捕获 Panic -> 等待执行结束 -> 返回结果”的完整流程。
 *
 * 3. 关键点精讲：
 *    - Goroutine 隔离：代码在新的 goroutine 中执行，配合 recover 确保 panic 不会逃逸。
 *    - defer + recover：这是 Go 中捕获 panic 的标准范式。必须在 defer 中调用 recover()。
 *    - debug.Stack()：仅仅捕获 panic 的值（通常是 string）是不够的，堆栈信息对于定位问题至关重要。
 *    - sync.WaitGroup：虽然函数名带 "Async"，但使用了 wg.Wait()，说明这是一个“同步阻塞”的包装函数。
 *      它让调用者感觉像是在调用一个普通函数，但拥有了 crash 保护。
 *    - Channel 传递错误：使用 buffered channel (容量1) 来传递 panic 产生的 error。
 *      - 正常情况：errCh 为空，close 后读取返回 nil。
 *      - Panic 情况：errCh 有值，读取返回 error。
 *
 * 4. 改进建议：
 *    - Context 使用：当前的实现接收了 ctx 但没使用。实际场景中，runnable 最好也能感知 ctx，或者在 select 中等待 wg 和 ctx.Done()。
 *
 */

// AsyncExecutePanicToError 执行 runnable，捕获 panic 并转化为 error 返回
func AsyncExecutePanicToError(ctx context.Context, runnable func()) error {
	var wg sync.WaitGroup
	errCh := make(chan error, 1)

	wg.Add(1)
	go func() {
		defer func() {
			// 核心：捕获 Panic
			if r := recover(); r != nil {
				// 建议：带上堆栈信息，方便 Debug
				errCh <- fmt.Errorf("goroutine panic: %v\nStack Trace:\n%s", r, debug.Stack())
			}
			wg.Done()
		}()
		runnable()
	}()

	wg.Wait()    // 阻塞等待
	close(errCh) // 关闭通道

	return <-errCh // 读取错误（无错误则为 nil）
}

// 示例代码
func main() {
	ctx := context.Background()

	fmt.Println("=== Case 1: 正常执行 ===")
	err := AsyncExecutePanicToError(ctx, func() {
		fmt.Println("  Working normally...")
	})
	if err != nil {
		fmt.Printf("  Error: %v\n", err)
	} else {
		fmt.Println("  Success!")
	}

	fmt.Println("\n=== Case 2: 发生 Panic ===")
	err = AsyncExecutePanicToError(ctx, func() {
		fmt.Println("  About to panic...")
		panic("something went wrong!")
	})
	if err != nil {
		fmt.Printf("  Caught Error: %v\n", err) // 这里会打印包含堆栈的错误信息
	} else {
		fmt.Println("  Success!")
	}

	fmt.Println("\n=== Case 3: 发生空指针 Panic ===")
	err = AsyncExecutePanicToError(ctx, func() {
		var p *int
		*p = 1 // 空指针解引用
	})
	if err != nil {
		// 仅打印第一行错误信息，避免堆栈刷屏
		fmt.Printf("  Caught Error (short): %v...\n", err.Error()[:50])
	}
}
