https://google.github.io/googletest/primer.html

*** Intro

* 基础概念：
  * An assertion’s result can be *success*, *nonfatal failure* (EXPECT), or *fatal failure* (ASSERT).
  * test suite, test fixture class
    *  test命名不能带下划线，因为Gtest源码使用下划线将他们拼接为独立的类名


ASSERT_EQ(x.size(), y.size()) << "Vectors x and y are of unequal length";

for (int i = 0; i < x.size(); ++i) {
  EXPECT_EQ(x[i], y[i]) << "Vectors x and y differ at index " << i;
}

// Tests factorial of 0.
TEST(FactorialTest, HandlesZeroInput) {
  EXPECT_EQ(Factorial(0), 1);
}

// Tests factorial of positive numbers.
TEST(FactorialTest, HandlesPositiveInput) {
  EXPECT_EQ(Factorial(1), 1);
  EXPECT_EQ(Factorial(2), 2);
  EXPECT_EQ(Factorial(3), 6);
  EXPECT_EQ(Factorial(8), 40320);
}

-- InGtest(googletest/include/gtest/internal/gtest-internal.h) --
// Expands to the name of the class that implements the given test.
#define GTEST_TEST_CLASS_NAME_(test_suite_name, test_name) \                                                                                                      
  test_suite_name##_##test_name##_Test


class TestFixtureName : public ::testing::Test {
 protected:
  ...
  void SetUp();
  void TearDown();
};


*** Running

Running Test Programs: Advanced Options

* --gtests_list_tests
* `./foo_test --gtest_filter="FooTest.*:BarTest.*-FooTest.Bar:BarTest.Foo"`
  * 注意引号
* `TEST_FAIL_FAST` environment variable or `--gtest_fail_fast` flag
* To include disabled tests in test execution, just invoke the test program with the `--gtest_also_run_disabled_tests` flag or set the `GTEST_ALSO_RUN_DISABLED_TESTS` environment variable to a value other than `0`. You can combine this with the `--gtest_filter` flag to further select which disabled tests to run.
* Controlling How Failures Are Reported
  * TEST_PREMATURE_EXIT_FILE
  * **GTEST_BREAK_ON_FAILURE** 好用，适合debugger
  * Disabling Catching Test-Thrown Exceptions
  * Sanitizer support

$ foo_test --gtest_repeat=1000
Repeat foo_test 1000 times and don't stop at failures.'

$ foo_test --gtest_repeat=-1
A negative count means repeating forever.

$ foo_test --gtest_repeat=1000 --gtest_break_on_failure
Repeat foo_test 1000 times, stopping at the first failure.  This
is especially useful when running under a debugger: when the test
fails, it will drop into the debugger and you can then inspect
variables and stacks.

$ foo_test --gtest_repeat=1000 --gtest_filter=FooBar.*
Repeat the tests whose name matches the filter 1000 times.

--gtest_shuffle

GTEST_TOTAL_SHARDS、GTEST_SHARD_INDEX


*** usage

* 用std::cerr输出信息

* DCHECK
  * [DCHECK只在debug模式生效，用于先验知道生效的CHECK](https://groups.google.com/a/chromium.org/g/chromium-dev/c/LU6NWiaSSRc)
  * 配合bazel的 `-c dbg`

* capture stdout

testing::internal::CaptureStdout();
std::cout << "My test";
std::string output = testing::internal::GetCapturedStdout();


*** TEST_F


TEST_F(TestFixtureName, TestName) {
  ... test body ...
}


* different tests in the same test suite have different test fixture objects
* 是否使用 SetUp/TearDown，参考[FAQ](https://google.github.io/googletest/faq.html#CtorVsSetUp)
* TestFixtureName 常命名为 XxxTest


#include "gtest/gtest.h"

template <typename E>  // E is the element type.
class Queue {
 public:
  Queue();
  void Enqueue(const E& element);
  E* Dequeue();  // Returns NULL if the queue is empty.
  size_t size() const;
  ...
};

class QueueTest : public ::testing::Test {
 protected:
  void SetUp() override {
     q1_.Enqueue(1);
     q2_.Enqueue(2);
     q2_.Enqueue(3);
  }

  // void TearDown() override {}

  Queue<int> q0_;
  Queue<int> q1_;
  Queue<int> q2_;
};

TEST_F(QueueTest, IsEmptyInitially) {
  EXPECT_EQ(q0_.size(), 0);
}

TEST_F(QueueTest, DequeueWorks) {
  int* n = q0_.Dequeue();
  EXPECT_EQ(n, nullptr);

  n = q1_.Dequeue();
  ASSERT_NE(n, nullptr);
  EXPECT_EQ(*n, 1);
  EXPECT_EQ(q1_.size(), 0);
  delete n;

  n = q2_.Dequeue();
  ASSERT_NE(n, nullptr);
  EXPECT_EQ(*n, 2);
  EXPECT_EQ(q2_.size(), 1);
  delete n;
}

int main(int argc, char **argv) {
  signal(SIGPIPE, SIG_IGN);
  ::testing::InitGoogleTest(&argc, argv);
  return RUN_ALL_TESTS();
}


When invoked, the `RUN_ALL_TESTS()` macro:

* Saves the state of all googletest flags.
* Creates a test fixture object for the first test.
* Initializes it via `SetUp()`.
* Runs the test on the fixture object.
* Cleans up the fixture via `TearDown()`.
* Deletes the fixture.
* Restores the state of all googletest flags.
* Repeats the above steps for the next test, until all tests have run.


*** Advanced



https://google.github.io/googletest/advanced.html

* More Assertions
  * Explicit Success and Failure
    * `SUCCEED()`、`FAIL()`、`ADD_FAILURE`、`ADD_FAILURE_AT`
  * Exception Assertions
    * EXPECT_NO_THROW，{NO}{}{ANY}
  * Predicate Assertions for Better Error Messages
  * [`EXPECT_PRED_FORMAT*`](https://google.github.io/googletest/reference/assertions.html#EXPECT_PRED_FORMAT)
  * [Floating-Point Comparison](https://google.github.io/googletest/reference/assertions.html#floating-point)
  * Asserting Using Gmock Matchers
    * https://google.github.io/googletest/reference/assertions.html#EXPECT_THAT
  * More String Assertions
    * https://google.github.io/googletest/reference/matchers.html#string-matchers
  * Type Assertions
  * Assertion Placement
    * The one constraint is that assertions that generate a fatal failure (`FAIL*` and `ASSERT_*`) can only be used in void-returning functions.
    * 同样也不能用在构造/析构函数里


EXPECT_NO_THROW({
  int n = 5;
  DoSomething(&n);
});

namespace testing {

// Returns an AssertionResult object to indicate that an assertion has
// succeeded.
AssertionResult AssertionSuccess();

// Returns an AssertionResult object to indicate that an assertion has
// failed.
AssertionResult AssertionFailure();

}

testing::AssertionResult IsEven(int n) {
  if ((n % 2) == 0)
    return testing::AssertionSuccess();
  else
    return testing::AssertionFailure() << n << " is odd";
}

EXPECT_FALSE(IsEven(Fib(6))



* Type Assertions
::testing::StaticAssertTypeEq<T1, T2>();

template <typename T> class Foo {
 public:
  void Bar() { testing::StaticAssertTypeEq<int, T>(); }
};
void Test2() { Foo<bool> foo; foo.Bar(); }


* Skipping test execution

TEST(SkipTest, DoesSkip) {
  GTEST_SKIP() << "Skipping single test";
  EXPECT_EQ(0, 1);  // Won't fail; it won't be executed
}

class SkipFixture : public ::testing::Test {
 protected:
  void SetUp() override {
    GTEST_SKIP() << "Skipping all tests for this fixture";
  }
};

// Tests for SkipFixture won't be executed.
TEST_F(SkipFixture, SkipsOneTest) {
  EXPECT_EQ(5, 7);  // Won't fail
}

* asan

extern "C" {
void __ubsan_on_report() {
  FAIL() << "Encountered an undefined behavior sanitizer error";
}
void __asan_on_error() {
  FAIL() << "Encountered an address sanitizer error";
}
void __tsan_on_report() {
  FAIL() << "Encountered a thread sanitizer error";
}
}  // extern "C"
