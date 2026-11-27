[toc]

> https://m.youtube.com/watch?v=ZAji7PkXaKY
>
> back to basics系列

### Intro

* Standard C++   =  C++ Language + Standard Library

### 《Effective Modern C++》, Scott Meyers 

**Intro**

* lvalue: 和地址密切联系，all parameters are lvalues
* function object可以是定义了operator ()的object，只要有function-calling syntax就行
* deprecated feature: `std::auto_ptr -> std::unique_ptr`
* Undefined behavior: 数组越界、dereferencing an uninitialized iterator、engaging in a data race

#### chpt 1 Deducing Types

deducing types的机制：

* c++98: function template 

  =>

* c++11: auto, decltype

  =>

* c++14: decltype(auto)

##### Item 1: Understand template type deduction 、Constexpr

auto的deduction机制和template type deduction紧密相联

模版类型推断是综合性的，不止和T相关，也和ParamType相关(adornments)，有三种情形

```c++
template<typename T> 
void f(ParamType param);

f(expr); // deduce T and ParamType from expr
```

* Case 1: **ParamType** is a Reference or Pointer, but not a Universal Reference
* Case 2: **ParamType** is a Universal Reference
  * 右值->右值引用；左值->左值引用

  * 唯一T会deduce为引用的场景
* Case 3: **ParamType** is Neither a Pointer nor a Reference 
  * Param will be a copy
     * 去除 const、&、volatile等修饰
  * ` const char* const ptr =  // ptr is const pointer to const object
     "Fun with pointers";` 保留左边的const
* array arguments
  
  * the type of an array that’s passed to a template function by value is deduced to be a pointer type
  * 需要注意数组传引用的时候不一样！存在数组引用`constchar(&)[13]`  => 利用它来**推断数组大小**

```c++
// return size of an array as a compile-time constant. (The
// array parameter has no name, because we care only about
// the number of elements it contains.)
template<typename T, std::size_t N> // see info 
constexpr std::size_t arraySize(T (&)[N]) noexcept // below on 
{																									// constexpr
	return N; // and
}// noexcept

int keyVals[] = { 1, 3, 7, 9, 11, 22, 35 };      // keyVals has 7 elements
int mappedVals[arraySize(keyVals)]; // so does mappedVals

std::array<int, arraySize(keyVals)> mappedVals; // mappedVals' size is 7


static_assert(arraySize(keyVals) == 7);
类内定义
constexpr static double keyVals[] = {1,2,3,4,5,6,7}
```





##### Item 2: Understand **auto** type deduction.

原则：只有明确需要 copy 才使用 auto，其它需要 auto 的情况用 auto*, auto&

* `A& g(); auto a = g(); A a = g();`



```c++
template<typename T> 
void f(ParamType param);

f(expr); // deduce T and ParamType from expr
```

auto对应T，type specifier对应ParamType，因此同Item1，也有三个cases，但有一个exception

唯一的exception：`auto x = { 20 }; `  the deduced type is a std::initializer_list，如果里面元素类型不一致，不会编译
* the only real difference between auto and template type deduction is that auto assumes that a braced initializer represents a std::initializer_list, but template type deduction doesn’t

Things to Remember
* auto type deduction is usually the same as template type deduction, but auto type deduction assumes that a braced initializer represents a `std::initializer_list`, and template type deduction doesn’t.
* auto in a function return type or a lambda parameter implies template type deduction, not auto type deduction.

##### Item 3: Understand decltype.

In C++11, perhaps the primary use for decltype is declaring function templates where the function’s return type depends on its parameter types.

* the type returned by a container’s operator[] depends on the container，比如`vector<bool>`返回的不是引用
  * c++14甚至可以不需要->，用模版判断，但存在无法引用的问题

```c++
template<typename Container, typename Index>  // works, but requires 			
auto authAndAccess(Container& c, Index i)     // refinement
	-> decltype(c[i])
{
  authenticateUser();
  return c[i];
}

template<typename Container, typename Index> // C++14; works,
decltype(auto)															 // but still requires 
authAndAccess(Container& c, Index i)				 // refinement
{
  authenticateUser();
  return c[i];
}


```

* decltype(auto)利用decltype rule，帮助单独的auto返回引用
  * 本质上是因为auto难以识别type specifier
  * decltype(**(x)**) is therefore int&. Putting parentheses around a name can change the type that decltype reports for it!

##### Item 4: Know how to view deduced types.

```c++
template<typename T>       // declaration only for TD;
class TD;                  // TD == "Type Displayer"

TD<decltype(x)> xType;     // elicit errors containing
TD<decltype(y)> yType;     // x's and y's types

///
std::cout << typeid(x).name() << '\n'; // display types for std::cout << typeid(y).name() << '\n'; // x and y
```

`std::type_info::name` 对模版中变量类型的判断不准

```c++
#include <boost/type_index.hpp>
template<typename T>
void f(const T& param)
{
  using std::cout;
  using boost::typeindex::type_id_with_cvr;
  
  // show T
  cout << "T = "<< type_id_with_cvr<T>().pretty_name() << '\n';
  // show param's type
  cout << "param = "<< type_id_with_cvr<decltype(param)>().pretty_name() 
    	 << '\n'; 
}
```

#### chpt 2 auto

##### Item 5: Prefer auto to explicit type declarations.
```c++
template<typename It>
void dwim(It b, It e)
{
  while (b != e) {
// algorithm to dwim ("do what I mean")
// for all elements in range from
// b to e
		typename std::iterator_traits<It>::value_type 
			currValue = *b;
	} 
}
```

auto必须初始化，潜在地避免未初始化的问题

```c++
auto derefUPLess =
[](const std::unique_ptr<Widget>& p1,
const std::unique_ptr<Widget>& p2) 
{ return *p1 < *p2; };

// C++14内部也可用auto

std::function<bool(const std::unique_ptr<Widget>&, const std::unique_ptr<Widget>&)>
derefUPLess = [](const std::unique_ptr<Widget>& p1, const std::unique_ptr<Widget>& p2)
               { return *p1 < *p2; };

// std::function相比auto占用内存多，效率低（对象统一进行了转化）
```

##### Item 6: Use the explicitly typed initializer idiom when **auto** deduces undesired types.

有关`vector<bool>`：because operator[] for `std::vector<T>` is supposed to return a T&, but C++ forbids references to bits.

`std::vector<bool>::reference` is an example of a proxy class: a class that exists for the purpose of emulating and augmenting the behavior of some other types

proxy class
* invisible: `vector<bool>`
* apparent: `std::shared_ptr, std::unique_ptr`
* expression templates: `Matrix sum = m1 + m2 + m3 + m4;`



#### chpt 3 Moving to Modern C++

##### Item 7: Distinguish between () and {} when creating objects.

`std::vector<int> v{ 1, 3, 5 }; // v's initial content is 1, 3, 5`

**特性**：

* uncopyable objects (e.g., std::atomics—see Item 40) 

`std::atomic<int> ai1{ 0 }; // fine`

*  it prohibits implicit *narrowing conversions* among built-in types
*  immunity to C++’s *most vexing parse*
  * A side effect of C++’s rule that anything that can be parsed as a declaration must be interpreted as one

**缺点**：

* the unusually tangled relationship among braced initializers, std::initializer_lists, and constructor overload resolution

  * `Widget(std::initializer_list<long double> il);`对{}的优先级极高，只有在实在转换不了的情况下才会用non-std::initializer_list constructors
  * Empty braces mean no arguments, not an empty std::initializer_list
  * vector对{}和()初始化的区分是不合理的
  * 因此：重载initializer_list参数的函数尤其要谨慎

  

##### Item 8: Prefer nullptr to 0 and NULL.

1. 0和NULL混用带来函数重载问题 -> counterintuitive behavior 
2. nullptr’s advantage is that it doesn’t have an integral type, but you can think of it as a pointer of *all* types
3. NULL和0在template type deduction中问题更严重

##### Item 9: Prefer alias declarations to typedefs.

```c++
template<typename T> // MyAllocList<T> 
using MyAllocList = std::list<T, MyAlloc<T>>; // is synonym for
                                                  // std::list<T,
                                                  //   MyAlloc<T>>
MyAllocList<Widget> lw; // client code


template<typename T> // MyAllocList<T>::type 
struct MyAllocList { // is synonym for std::list<T, MyAlloc<T>>
	typedef std::list<T, MyAlloc<T>> type;
};
MyAllocList<Widget>::type lw;           // client code

template<typename T>
class Widget {
 private:
	typename MyAllocList<T>::type list;
...
};


```

using的优势是能让编译器知道这是一个type，尤其在模版的使用中，避免混淆`MyAllocList<T>::type`

 template metaprogramming (TMP)

* C++11中的type traits是用typedef实现的，因此使用的时候要在前面声明`typename`

```c++
std::remove_const<T>::type					// yields T from const T
std::remove_reference<T>::type			// yields T from T& and T&&
std::add_lvalue_reference<T>::type	// yields T& from T
  
std::remove_const_t<T>
std::remove_reference_t<T>
std::add_lvalue_reference_t<T>
  
  
template <class T>
using remove_const_t = typename remove_const<T>::type;

template <class T>
using remove_reference_t = typename remove_reference<T>::type;

template <class T>
using add_lvalue_reference_t =
	typename add_lvalue_reference<T>::type;

```


##### Item 10: Prefer scoped **enum**s to unscoped **enum**s.

```c++
enum class Color { black, white, red };
auto c = Color::white;

enum Color;               // error!
enum class Color;         // fine
```

=> The reduction in namespace pollution 

=> There are no implicit conversions from enumerators in a scoped enum to any other type

=> scoped enums may always be forward-declared, unscoped enums只有指定了underlying type才可以

* 普通的enum默认是char，编译器需要选类最小的类型=> unscoped enums不需要大部分重新编译
* Scoped enums默认类型int，可指定

```c++
enum class Status: std::uint32_t; // underlying type for
																	// Status is std::uint32_t
                                  // (from <cstdint>)

```

unscoped enum更好的少数场景，uiEmail有implicit转换为size_t
```c++
enum UserInfoFields { uiName, uiEmail, uiReputation };
   UserInfo uInfo;                        // as before
   ...
auto val = std::get<uiEmail>(uInfo); // ah, get value of // email field


enum class UserInfoFields { uiName, uiEmail, uiReputation };
   UserInfo uInfo;                        // as before
   ...
auto val = std::get<static_cast<std::size_t>(UserInfoFields::uiEmail)>(uInfo);
```
如果用函数转，需要constexpr
```c++
template<typename E>
constexpr typename std::underlying_type<E>::type
	toUType(E enumerator) noexcept
{
	return static_cast<typename std::underlying_type<E>::type>(enumerator);
}
```

c++14可以用` static_cast<std::underlying_type_t<E>>(enumerator)`

```c++
template<typename E> // C++14 
constexpr auto
	toUType(E enumerator) noexcept
{
	return static_cast<std::underlying_type_t<E>>(enumerator); 
}
auto val = std::get<toUType(UserInfoFields::uiEmail)>(uInfo);
```



##### Item 11: Prefer deleted functions to private undefined ones.

e.g.: std::basic_ios，禁止copy streams

相比undefined private function

* 错误信息更清晰
* 可以delete非成员函数

* 针对模版

```c++
template<typename T>
void processPointer(T* ptr);

template<>
void processPointer<void>(void*) = delete;
template<>
void processPointer<char>(char*) = delete;
template<>
void processPointer<const void>(const void*) = delete;
template<>
void processPointer<const char>(const char*) = delete;

// const volatile char*, const volatile void*, std::wchar_t, std::char16_t, std::char32_t.

//如果在类内定义
template<>
void Widget::processPointer<void>(void*) = delete;
```



##### Item 12: Declare overriding functions **override**.

```c++
class Base {
public:
  virtual void doWork();
...
};
class Derived: public Base {
public:
  virtual void doWork();
...
};
std::unique_ptr<Base> upb = std::make_unique<Derived>();
upb->doWork();
// derived class function is invoked
```

* override的各种要求，还包括reference qualifier
* 改变signature方便看有多少依赖
* Applying **final** to a virtual function prevents the function from being overridden in derived classes. final may also be applied to a class, in which case the class is prohibited from being used as a base class.

*  Member function reference qualifiers make it possible to treat lvalue and rvalue objects (*this) differently.

```c++
class Widget {
public:
  using DataType = std::vector<double>;
  DataType& data() & { return values; }
  DataType data() && { return std::move(values); } ...
  private:
    DataType values;
};
```

##### Item 13: Prefer **const_iterator**s to **iterator**s.

**pointer-to-const == const_iterators**

there’s no portable conversion from a `const_iterator` to an `iterator`, not even with a `static_cast`. Even the semantic sledgehammer known as `reinterpret_cast` can’t do the job. 

```c++
std::vector<int> values; // as before ...
auto it = // use cbegin
	std::find(values.cbegin(),values.cend(), 1983); // and cend
values.insert(it, 1998);
```

```c++
template<typename C, typename V>
void findAndInsert(C& container,
{
  const V& targetVal,
  const V& insertVal)
  using std::cbegin;
  using std::cend;
  auto it = std::find(cbegin(container), cend(container),
  targetVal);
  container.insert(it, insertVal); 
}
                   
template <class C>
auto cbegin(const C& container)->decltype(std::begin(container)) {
  return std::begin(container);         // see explanation below
}
```

Non-member cbegin只有C++14才有；C++11中，即使是vector非const，begin返回的带const引用的vector也会是const_iterator类型



##### Item 14: Declare functions **noexcept** if they won’t emit exceptions.

noexcept意味着函数行为const

e.g. C++11，`vector.push_back(std::move(XX))`可能违反异常安全性（比如vector重新申请内存的场景），`std::vector::push_back` takes advantage of this “move if you can, but copy if you must” strategy，依据是否declared noexcept来判断

* 内部实现-> `std::move_if_noexcept` -> `std::is_nothrow_move_constructible`

```c++
template <class T, size_t N>
void swap(T (&a)[N], // see
					T (&b)[N]) noexcept(noexcept(swap(*a, *b))); // below

template <class T1, class T2>
struct pair {
	...
	void swap(pair& p) noexcept(noexcept(swap(first, p.first)) && 						   								 					noexcept(swap(second, p.second)));
	...
};
```

* Wide contract functions更适合noexcept，因为没有后续调试抛出异常的需求

>Things to Remember
>
>• noexcept is part of a function’s interface, and that means that callers may depend on it.
>
>• noexcept functions are more optimizable than non-noexcept functions.
>
>• noexcept is particularly valuable for the move operations, swap, memory deallocation functions, and destructors.
>
>• Most functions are exception-neutral rather than noexcept.



##### Item 15: Use **constexpr** whenever possible.

* translation时知晓，包括compilation和linking
* constexpr变量声明时需要初始化
  * 类内constexpr变量需要额外定义
    * https://stackoverflow.com/questions/8016780/undefined-reference-to-static-constexpr-char
    * `constexpr int A::n;` in cpp file

* constexpr function，用法参考Item 1
  * c++11只能写一句return

```c++
constexpr
int pow(int base, int exp) noexcept
{
...
}
constexpr auto numConds = 5;
std::array<int, pow(3, numConds)> results;

constexpr int pow(int base, int exp) noexcept     //c++11
{
	return (exp == 0 ? 1 : base * pow(base, exp - 1)); 
}

constexpr int pow(int base, int exp) noexcept
{
  auto result = 1;
  for (int i = 0; i < exp; ++i) result *= base;
  return result;
}

```

P100: 自定义的类型也可以constexpr

* C++14中即使是Point.set也可以constexpr



##### Item 16: Make **const** member functions thread safe.

```c++
class Polynomial {
  public:
    using RootsType = std::vector<double>;
    RootsType roots() const
    {
      std::lock_guard<std::mutex> g(m);
      if (!rootsAreValid) {
        ...
        rootsAreValid = true;
      }
      return rootVals;
    }
  private:
  	mutable std::mutex m;
    mutable bool rootsAreValid{ false };
    mutable RootsType rootVals{};
};
```

私有成员`mutable std::atomic<unsigned> callCount{ 0 };`适合用于计数

* std::mutex和std::atomic都是move-only types，不能copy
  * 如果想定义一个数组，数组中的对象包含atomic类型，不能用vector直接构造（因为会调用复制构造函数），可以构造`vector<shared_ptr<Object>>`
  * atomic适合递增操作，但如果是先运算后赋值，可能出现竞争
  * mutable 字段，表示“这个成员变量不算对象内部状态”，不禁止const函数修改它

```c++
class Widget {
public:
...
  int magicValue() const
  {
    std::lock_guard<std::mutex> guard(m);
    if (cacheValid) return cachedValue;
    else {
      auto val1 = expensiveComputation1();
      auto val2 = expensiveComputation2();
      cachedValue = val1 + val2;
      cacheValid = true;
      return cachedValue;
    }
	}
private:
  mutable std::mutex m;
  mutable int cachedValue;
  mutable bool cacheValid{ false };
};
```



##### Item 17: Understand special member function generation

问题的来源：memberwise move的思路，move能move的，剩下的copy

**special member functions**: 

* c++98: the default constructor, the destructor, the copy constructor, and the copy assignment operator
* c++11: the move constructor and the move assignment operator
  * 和copy constructor的区别在于，c++11的这两个fucntion是dependent的
  * 如果有explicit copy constructor，move constructor不会自动生成

*the rule of three*: copy constructor, copy assignment operator, or destructor

动机：the rule of three 和 move/copy 的 dependent 特性有冲突 => C++11 does *not* generate move operations for a class with a user-declared destructor

`=default`和`=delete`，前者在自己有写构造函数的情况下生成默认构造函数，减小代码量，后者禁止函数

```c++
//! moving is allowed; copying is disallowed; default construction not possible
//!@{
~TCPConnection();  //!< destructor sends a RST if the connection is still open
TCPConnection() = delete;
TCPConnection(TCPConnection &&other) = default;
TCPConnection &operator=(TCPConnection &&other) = default;
TCPConnection(const TCPConnection &other) = delete;
TCPConnection &operator=(const TCPConnection &other) = delete;
//!@}
```

Note: Member function templates never suppress generation of special member functions.





#### chpt 4 Smart Pointers

##### Item 18: Use std::unique_ptr for exclusive-ownership resource management.

* unique_ptr is a move-only type
* also applied to the Pimpl Idiom (Item 22)
* 还有`std::unique_ptr<T[]>`
  * About the only situation I can conceive of when a `std::unique_ptr<T[]>` would make sense would be when you’re using a C-like API that returns a raw pointer to a heap array that you assume ownership of.
* `std::shared_ptr<Investment> sp = makeInvestment( arguments );` 

```c++
class Investment {
public:
  virtual ~Investment();
};
class Stock:
public Investment { ... };
class Bond:
public Investment { ... };
class RealEstate:
public Investment { ... };

template<typename... Ts> std::unique_ptr<Investment> makeInvestment(Ts&&... params);

{
	auto pInvestment = // pInvestment is of type 
		makeInvestment( arguments ); // std::unique_ptr<Investment>
}// destroy *pInvestment
```

```c++
auto delInvmt = [](Investment* pInvestment)
                {
                  makeLogEntry(pInvestment);
                  delete pInvestment;
                };

template<typename... Ts>
std::unique_ptr<Investment, decltype(delInvmt)> // 如果是C++14，返回值可以用auto，delInvmt的定义也可放入makeInvestment函数内
makeInvestment(Ts&&... params) {
	std::unique_ptr<Investment, decltype(delInvmt)> pInv(nullptr, delInvmt);
  if ( /* a Stock object should be created */ ){
		pInv.reset(new Stock(std::forward<Ts>(params)...)); 
  }
  else if ( /* a Bond object should be created */ ){
		pInv.reset(new Bond(std::forward<Ts>(params)...)); 
  }
  else if ( /* a RealEstate object should be created */ ){
		pInv.reset(new RealEstate(std::forward<Ts>(params)...)); 
  }
  return pInv;
}

```

代码细节：

* `std::forward`: 为了在使用右值引用参数的函数模板中解决参数的perfect-forward问题。(Item 25), [reference](https://blog.csdn.net/zhangsj1007/article/details/81149719?utm_medium=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-6.edu_weight&depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromMachineLearnPai2-6.edu_weight)
* unique_ptr可以作为函数返回值
* 不能直接给unique_ptr赋值裸指针，`reset(new)`是标准用法
* 引入deleter后unique_ptr的size变化：如果是函数指针，1 word -> 2 word；如果是函数对象，取决于函数内部的state



##### Item 19: Use std::shared_ptr for shared-ownership resource management.

dynamically allocated control blocks, arbitrarily large deleters and allocators, virtual function machinery, and atomic reference count manipulations

[shared_ptr的使用](https://blog.csdn.net/qq_33266987/article/details/78784852), [一篇看不太懂的shared_ptr使用技巧](https://gist.github.com/BruceChen7/8cccb33ea6fbc73a0651c4bce3166806)

As with garbage collection, clients need not concern themselves with managing the life‐ time of pointed-to objects, but as with destructors, the timing of the objects’ destruc‐ tion is deterministic.

reference count的影响：

* std::shared_ptrs are twice the size of a raw pointer
* Memory for the reference count must be dynamically allocated，除非用`std::make_shared`
* Increments and decrements of the reference count must be atomic

=> move assignment is faster than copy assignment

![shared-ptr](C++/shared-ptr.png)

对于custom deleter，和unique_ptr的区别在于deleter不影响shared_ptr的类型

* 这样便于函数传参、放入同一容器
* 始终two words size：

```c++
auto loggingDel = [](Widget *pw){
                    makeLogEntry(pw);
										delete pw; 
									};
std::unique_ptr<Widget, decltype(loggingDel) > upw(new Widget, loggingDel);
std::shared_ptr<Widget> spw(new Widget, loggingDel);
// deleter type is not part of ptr type
```

关于control block的rules

* std::make_shared (see Item 21) always creates a control block
* A control block is created when a std::shared_ptr is constructed from a unique-ownership pointer (i.e., a std::unique_ptr or std::auto_ptr).
* When a std::shared_ptr constructor is called with a raw pointer, it creates a control block

=> 

* 用同一个裸指针创建两个shared_ptr是undefined behaviour
  * 正确写法：

```c++
std::shared_ptr<Widget> spw1(new Widget);
std::shared_ptr<Widget> spw2(spw1);
```

* 类似地，不要用this指针创建shared_ptr

  * 正确写法：*The Curiously Recurring Template Pattern (CRTP)*
  * 注意 shared_from_this() 必须在对象生成 shared_ptr 后调用
    * 为了防止process一个不存在shared_ptr的对象，常把ctors设成private
    * shared_from_this() 不能在构造函数里调用，在构造时它还没有交给 shared_ptr 接管

```c++
class Widget: public std::enable_shared_from_this<Widget> {
public:
  // factory function that perfect-forwards args to a private ctor
	template<typename... Ts>
	static std::shared_ptr<Widget> create(Ts&&... params);
	void process(){
    processedWidgets.emplace_back(shared_from_this());
  }
private:
  Widget Widget();
  Widget(Widget &&other);
  Widget(const Widget &other);
  TCPConnection() = delete;
};
```



**Warn:**

* `std::vector<std::shared_ptr<A> > a_vec(n, std::make_shared<A>());`这个用法是错的，会给里面元素赋值同一个智能指针，正确写法如下：

```c++
std::vector<std::shared_ptr<A>> a(size);
std::for_each(std::begin(a), std::end(a),[](std::shared_ptr<A> &ptr) {
                    ptr = std::make_shared<A>();
```

* shared_ptr没有array的版本。一律建议用std::vector
* shared_ptr不能循环指向，会永不析构内存泄漏



##### Item 20: Use std::weak_ptr for std::shared_ptr-like pointers that can dangle.

weak_ptr指示shared_ptr是否dangle，但不能直接dereference，需要一个原子操作(lock)，衔接判断和取值

* Potential use cases for `std::weak_ptr` include caching, observer lists, and the prevention of std::shared_ptr cycles.

```c++
auto spw = std::make_shared<Widget>();
std::weak_ptr<Widget> wpw(spw);
spw = nullptr;
if (wpw.expired()) ...
auto spw2 = wpw.lock();
std::shared_ptr<Widget> spw3(wpw); // if wpw's expired, throw std::bad_weak_ptr
```

应用：读写cache，自动删去不再使用的对象

```c++
std::unique_ptr<const Widget> loadWidget(WidgetID id);
```

=>

```c++
std::shared_ptr<const Widget> fastLoadWidget(WidgetID id) {
	static std::unordered_map<WidgetID, std::weak_ptr<const Widget>> cache;
	auto objPtr = cache[id].lock();
  if (!objPtr) {
    objPtr = loadWidget(id);
    cache[id] = objPtr;
	}
  return objPtr;
}

//优化空间：删除cache内不用的weak_ptr
```



##### Item 21: Prefer **std::make_unique** and **std::make_shared** to direct use of **new**.

https://en.cppreference.com/w/cpp/memory/unique_ptr/make_unique

C++14没有`make_unique`

* 参数只能是 unbounded array： `std::unique_ptr<Vec3[]> v3 = std::make_unique<Vec3[]>(5);`


```c++
// C++14 make_unique
namespace detail {
template<class>
constexpr bool is_unbounded_array_v = false;
template<class T>
constexpr bool is_unbounded_array_v<T[]> = true;
 
template<class>
constexpr bool is_bounded_array_v = false;
template<class T, std::size_t N>
constexpr bool is_bounded_array_v<T[N]> = true;
} // namespace detail
 
template<class T, class... Args>
std::enable_if_t<!std::is_array<T>::value, std::unique_ptr<T>>
make_unique(Args&&... args)
{
    return std::unique_ptr<T>(new T(std::forward<Args>(args)...));
}
 
template<class T>
std::enable_if_t<detail::is_unbounded_array_v<T>, std::unique_ptr<T>>
make_unique(std::size_t n)
{
    return std::unique_ptr<T>(new std::remove_extent_t<T>[n]());
}
 
template<class T, class... Args>
std::enable_if_t<detail::is_bounded_array_v<T>> make_unique(Args&&...) = delete;
```

```c++
std::allocate_shared
auto spw1(std::make_shared<Widget>());   //能用auto
```



**`make_shared`优点**

* 不用的话，有潜在的内存泄漏风险，和异常安全性有关
  * 先new再创建shared_ptr，如果在这中间computePriority抛出异常，则内存泄漏

```c++
processWidget(std::shared_ptr<Widget>(new Widget), computePriority());
```

* `make_shared`更高效，一次分配对象和control block的内存



**`make_shared`的缺点**

* deleter
* `make_shared`的perfect forwarding code用`()`，而非`{}`; `{}`只能用new，除非参考Item 2
```c++
// create std::initializer_list
auto initList = { 10, 20 };
// create std::vector using std::initializer_list ctor
auto spv = std::make_shared<std::vector<int>>(initList);
```

* using make functions to create objects of types with class-specific versions of operator new and operator delete is typically a poor idea. 因为只能new/delete本对象长度的内存，而非加上control block的
* shared_ptr的场景，必须要所有相关weak_ptr全destroy，指针控制块的内存才会释放



因为上述原因，想用new

```c++
std::shared_ptr<Widget> spw(new Widget, cusDel);
processWidget(std::move(spw), computePriority()); // both efficient and exception safe
```

##### Item 22: When using the Pimpl Idiom, define special member functions in the implementation file.

设计模式：减少client（只include .h文件）的相关编译

`widget.h`

```c++
class Widget {
public:
	Widget(); 
	~Widget(); 
	...
private:
  struct Impl;
  Impl *pImpl;
};
```

`widget.cpp`

```c++
#include "widget.h" 
#include "gadget.h" 
#include <string> 
#include <vector>
struct Widget::Impl {
  std::string name;
  std::vector<double> data;
  Gadget g1, g2, g3;
};
Widget::Widget() : pImpl(new Impl) {}
Widget::~Widget() { delete pImpl; }
```

**新的用`unique_ptr`的版本**

* 不要在.h文件里generate析构函数

`widget.h`

```c++
class Widget {
public:
	Widget(); 
  ~Widget();
  Widget(Widget&& rhs);
  Widget& operator=(Widget&& rhs);
private:
  struct Impl;
  std::unique_ptr<Impl> pImpl;
};
```

`widget.cpp`

```c++
#include "widget.h" 
#include "gadget.h" 
#include <string> 
#include <vector>
struct Widget::Impl {
  std::string name;
  std::vector<double> data;
  Gadget g1, g2, g3;
};
Widget::Widget(): pImpl(std::make_unique<Impl>()) {}
Widget::~Widget() = default;
Widget::Widget(Widget&& rhs) = default;
Widget& Widget::operator=(Widget&& rhs) = default;
Widget::Widget(const Widget& rhs)
: pImpl(std::make_unique<Impl>(*rhs.pImpl)) {}
Widget& Widget::operator=(const Widget& rhs)
{
	*pImpl = *rhs.pImpl;
  return *this;
}
```

如果是shared_ptr，则不需要做任何操作，本质上是因为unique_ptr的deleter在类型定义中，为了更高效的runtime行为，隐性地generate一些function





#### chpt 5 Rvalue References, Move Semantics, and Perfect Forwarding

Rvalue references => Move Semantics and Perfect Forwarding

it’s especially important to bear in mind that a parameter is always an lvalue, even if its type is an rvalue reference

##### Item 23: Understand **std::move** and **std::forward**.

`std::move` doesn’t move anything. `std::forward` doesn’t forward anything

`std::move` unconditionally casts its argument to an rvalue, while `std::forward` performs this cast only if a particular condition is fulfilled

```c++
template<typename T> 
decltype(auto) move(T&& param) {
	using ReturnType = remove_reference_t<T>&&;
	return static_cast<ReturnType>(param); 
} // C++14
// remove_reference是因为Item 1 => T有可能被推断为lvalue reference
```

First, don’t declare objects const if you want to be able to move from them. Move requests on const objects are silently transformed into copy operations. 

Second, std::move not only doesn’t actually move anything, it doesn’t even guarantee that the object it’s casting will be eligible to be moved. The only thing you know for sure about the result of applying std::move to an object is that it’s an rvalue.

```c++
void process(const Widget& lvalArg);
void process(Widget&& rvalArg);
template<typename T>
void logAndProcess(T&& param) {
	auto now = std::chrono::system_clock::now();
  makeLogEntry("Calling 'process'", now);
	process(std::forward<T>(param));
}

Widget w;
logAndProcess(w);                  // call with lvalue
logAndProcess(std::move(w));       // call with rvalue
```

`std::forward`: a *conditional* cast, it casts to an rvalue only if its argument was initialized with an rvalue. 原理参考Item 28



##### Item 24: Distinguish universal references from rvalue references.

T&&不一定是rvalue references，称其为universal references。用右值初始化即为右值引用，用左值初始化即为左值引用。

场景如下：

* 模板: 

```c++
template<typename T>
void f(T&& param); // param is a universal reference
```

* auto: `auto&& var2 = var1; // var2 is a universal reference`

universal reference的场景有限制：

* 必须是T&&，加const也不行
* 必须有type deduction，e.g. `push_back` 's caller explicitly specifies the type，type deduction，而`emplace_back`有

```c++
template<class T, class Allocator = allocator<T>>  // from C++
class vector {                                     // Standards
public:
	void push_back(T&& x);
	...
};
template<class T, class Allocator = allocator<T>>  
class vector {
public:
	template <class... Args>
	void emplace_back(Args&&... args); ...
};
```

universal reference的应用：

```c++
auto timeFuncInvocation = [](auto&& func, auto&&... params){
  start timer;
  std::forward<decltype(func)>(func)( std::forward<decltype(params)>(params)... );
  stop timer and record elapsed time;
};
```



##### Item 25: Use **std::move** on rvalue references, **std::forward** on universal references.

std::forward 的动机是 conditionally cast

Perfect forwarding is often used with [variadic templates](http://en.cppreference.com/w/cpp/language/parameter_pack) to wrap calls to functions with an arbitrary number of arguments. For example, [`std::make_unique`](http://en.cppreference.com/w/cpp/memory/unique_ptr/make_unique) and [`std::make_shared`](http://en.cppreference.com/w/cpp/memory/shared_ptr/make_shared) both use perfect forwarding to forward their arguments to the constructor of the wrapped type.

Universal reference 的其中一个动机是替代“同时 overload lvalue、rvalue references”，后者的缺点是：1）某些场景的潜在开销；2）代码volume；3）scalability，多参数函数的拓展

```c++
Matrix // by-value return 
operator+(Matrix&& lhs, const Matrix& rhs) {
	lhs += rhs;
  return std::move(lhs);
}

template<typename T>
Fraction reduceAndCopy(T&& frac) {
	frac.reduce();
	return std::forward<T>(frac);
}
```

Never apply `std::move` or `std::forward` to local objects if they would otherwise be eligible for the return value optimization.

* copy elision
* RVO 生效的要求
  * 类型一致
  * the local object is what’s being returned，比如不能是 referenced type、或函数参数
  * unnamed (named->NRVO)
* 永远无需 move 的原因："if the conditions for the RVO are met, but compilers choose not to perform copy elision, the object being returned *must be treated as an rvalue*."

##### Item 26: Avoid overloading on universal references.

* Overloading on universal references almost always leads to the universal reference overload being called more frequently than expected.
* Perfect-forwarding constructors are especially problematic, because they’re typically better matches than copy constructors for non-const lvalues, and they can hijack derived class calls to base class copy and move constructors.
  * 即使 compilers 因 Item 17 生成了相关构造函数，依然存在优先级低于 overloaded universal references 的情况

##### Item 27: Familiarize yourself with alternatives to overloading on universal references.

* Abandon overloading
* Pass by const T&
* Pass by value

```c++
class Person {
 public:
	explicit Person(std::string n) : name(std::move(n)) {}
  explicit Person(int idx) : name(nameFromIdx(idx)) {}
  ...
private:
  std::string name;
};
```

* Use Tag dispatch

```c++
std::multiset<std::string> names;      // global data structure
template<typename T>                   // make log entry and add
void logAndAdd(T&& name)               // name to data structure
{
	auto now = std::chrono::system_clock::now();
  log(now, "logAndAdd");
  names.emplace(std::forward<T>(name));
}

=====>
  
template<typename T>
void logAndAdd(T&& name)
{
	logAndAddImpl(
		std::forward<T>(name),
		std::is_integral<typename std::remove_reference<T>::type>()
	); 
}

template<typename T>
void logAndAddImpl(T&& name, std::false_type) {
	auto now = std::chrono::system_clock::now();
  log(now, "logAndAdd");
  names.emplace(std::forward<T>(name));
}
// std::false_type(compile value) 而非 false(runtime value)

void logAndAddImpl(int idx, std::true_type) {
  logAndAdd(nameFromIdx(idx));
}
```

* Constraining templates that take universal references

```c++
class Person {
 public:
	template<typename T,
					 typename = typename std::enable_if<condition>::type>
	explicit Person(T&& n);
  
=>

class Person {
 public:
	template<typename T,
					 typename = typename std::enable_if<
												!std::is_same<Person,
																			typename std::decay<T>::type
																		 >::value
               				>::type
	>
  explicit Person(T&& n);
	...
};
  
=>

is_same -> is_base_of 进一步解决 Item 26 中派生类的问题
  
=>
  
c++14: typename -> _t后缀
  
=>
  
class Person {
 public:
	template<
		typename T,
		typename = std::enable_if_t<
			!std::is_base_of<Person, std::decay_t<T>>::value
			&&
			!std::is_integral<std::remove_reference_t<T>>::value
		>
	>
explicit Person(T&& n)
: name(std::forward<T>(n)) 
{
  // assert that a std::string can be created from a T object
	static_assert(
		std::is_constructible<std::string, T>::value, 
    "Parameter n can't be used to construct a std::string"
	);
  ...
}
explicit Person(int idx) : name(nameFromIdx(idx)) 
{... }
...
 private:
  std::string name;
};
```

Disadvantages：perfect forwarding has failure cases (Item 30) and baffling error messages



##### Item 28: Understand reference collapsing

> If either reference is an lvalue reference, the result is an lvalue reference. Otherwise (i.e., if both are rvalue references) the result is an rvalue reference.

Four contexts

*  template instantiation
* auto type generation
* the generation and use of typedefs and alias declarations (Item 9)
* decltype (Item 3)

=> the implementation of `std::forward`

```c++
template<typename T>
T&& forward(typename
							remove_reference<T>::type& param)
{
	return static_cast<T&&>(param);
}
```

=> 回顾 auto&&

=>

```c++
template<typename T>
class Widget {
 public:
  typedef T&& RvalueRefToT;
  ...
};
```



##### Item 29: Assume that move operations are not present, not cheap, and not used.

not cheap

*  `move std::array` runs in linear time
* `std::string ` 有SSO优化，小 string 存在对象内的 buffer 中，move 并不更快

not usable

*  The context in which the moving would take place requires a move operation that emits no exceptions, but that operation isn’t declared `noexcept`



##### Item 30: Familiarize yourself with perfect forwarding failure cases.

perfect forwarding 的含义：传递 type 信息，只针对 references

```c++
template<typename... Ts>
void fwd(Ts&&... params) {
  f(std::forward<Ts>(params)...)
}
```

应用：Item 42 (`std::make_unique`), Item 21 (`emplace`)

failure cases 的内在原因是 f 和 fwd 做的事情不一样

* Braced initializers：f有能力做转换，而fwd会类型推断失败
* 0 or NULL as null pointers
* Declaration-only integral **static const** data members
  * 硬件层面，指针和引用含义类似

```c++
class Widget {
 public:
	static const std::size_t MinVals = 28; // MinVals' declaration
	...
};


std::vector<int> widgetData; widgetData.reserve(Widget::MinVals); // use of MinVals

f(Widget::MinVals); // fine, treated as "f(28)"
fwd(Widget::MinVals); // error! shouldn't link

const std::size_t Widget::MinVals; // in Widget's .cpp file, remember to specify it only once
```

* Overloaded function names and template names
  * 本质上也是 fwd 没有能力推断函数信息

```c++
using ProcessFuncType = int (*)(int);
ProcessFuncType processValPtr = processVal;
fwd(processValPtr);
fwd(static_cast<ProcessFuncType>(workOnVal));
```

* Bitfields
  * Pointers to bitfields don't exist.

```c++
struct IPv4Header {
  std::uint32_t version:4,
                IHL:4,
                DSCP:6,
                ECN:2,
                totalLength:16;
  ...
};
void f(std::size_t sz); // function to call
IPv4Header h;
f(h.totalLength); // fine
fwd(h.totalLength); // error

// copy bitfield value; see Item 6 for info on init. form 
auto length = static_cast<std::uint16_t>(h.totalLength);
fwd(length); // forward the copy
```



#### chpt 6 Lambda Expressions

场景：

* STL algorithms, custom deleters, condition variables in threading API (Item 39)
* callback functions, interface adaptation functions, context-specific functions for one-off calls

概念：

* Compilation: lambda expressions, closure class
  * A *closure class* is a class from which a closure is instantiated. Each lambda causes compilers to generate a unique closure class. The statements inside a lambda become executable instructions in the member functions of its closure class.
* Runtime: closure
  * A *closure* is the runtime object created by a lambda. Depending on the capture mode, closures hold copies of or references to the captured data.

* Note
  * The **`mutable`** specification enables the body of a lambda expression to modify variables that are captured by value.
    * [ref](https://learn.microsoft.com/en-us/cpp/cpp/lambda-expressions-in-cpp?view=msvc-170)

##### Item 31: Avoid default capture modes

There are two default capture modes in C++11: by-reference and by-value. Default by-reference capture can lead to dangling references. Default by-value capture lures you into thinking you’re immune to that problem (you’re not), and it lulls you into thinking your closures are self-contained (they may not be).

```c++
using FilterContainer =
  std::vector<std::function<bool(int)>>;
FilterContainer filters;
void addDivisorFilter(){
  auto calc1 = computeSomeValue1();
  auto calc2 = computeSomeValue2();
  auto divisor = computeDivisor(calc1, calc2);
  filters.emplace_back(
  	[&](int value) { return value % divisor == 0; }
  ); 
}

template<typename C>
void workWithContainer(const C& container)
{
  auto calc1 = computeSomeValue1();
  auto calc2 = computeSomeValue2();
  auto divisor = computeDivisor(calc1, calc2);
  using ContElemT = typename C::value_type;
  using std::begin;
  using std::end;
  if (std::all_of(
  			begin(container), end(container),
    		[&](const ContElemT& value)
  			{ return value % divisor == 0; })
  	) {
  	...
  } else {
    ...
  }
}

// C++14
if (std::all_of(begin(container), end(container),
								[&](const auto& value)
                { return value % divisor == 0; }))
```

`auto`生成的`std::function`对象的大小更小，少在 fixed size in closure



Captures apply only to non-static local variables (including parameters) visible in the scope where the lambda is created. 

* default by-value capture 实质上捕获的是 Widget's this pointer => 无意间捕获 this

```c++
class Widget {
 public:
	...
  void addFilter() const;

 private:
	int divisor;
};
void Widget::addFilter() const {
	filters.emplace_back(
		[=](int value) { return value % divisor == 0; }
	);
}

===>
  
void Widget::addFilter() const {
	filters.emplace_back( // C++14:
		[divisor = divisor](int value) // copy divisor to closure 
    { return value % divisor == 0; } // use the copy
	);
}
```

An additional drawback to default by-value captures is that they can suggest that the corresponding closures are self-contained and insulated from changes to data outside the closures. In general, that’s not true, because lambdas may be dependent not just on local variables and parameters (which may be captured), but also on objects with *static storage duration*. 

```c++
void addDivisorFilter() {
	static auto calc1 = computeSomeValue1();
  static auto calc2 = computeSomeValue2();
	static auto divisor = computeDivisor(calc1, calc2);
	filters.emplace_back(
		[=](int value)
		{ return value % divisor == 0; }
	);
  ++divisor;
}
// 虽然lambda expression写的是by-value，实质上捕获的是reference
```



##### Item 32: Use init capture to move objects into closures.

generalized lambda capture，能捕获表达式的结果

e.g. for move-only object like `std::unique_ptr` or `std::future`

Using an init capture makes it possible for you to specify

* **the name of a data member** in the closure class generated from the lambda and
* **an expression** initializing that data member.

```c++
auto pw = std::make_unique<Widget>();
...
auto func = [pw = std::move(pw)]
						{ return pw->isValidated()
										 && pw->isArchived(); };
```

如果用 C++11 实现：

* moving the object to be captured into a function object produced by `std::bind` and
* giving the lambda a reference to the “captured” object.
  * `std::bind` -> a *bind* object
  * the lifetime of the bind object is the same as that of the closure

```c++
// C++14
std::vector<double> data;
...
auto func = [data = std::move(data)] { /* uses of data */ };

// C++11
std::vector<double> data;
...
auto func =
  std::bind(
		[](const std::vector<double>& data)
	  { /* uses of data */ }, 
  std::move(data)
);

auto func =
  std::bind(
		[](std::vector<double>& data) mutable
	  { /* uses of data */ }, 
  std::move(data)
);
```



##### Item 33: Use **decltype** on **auto&&** parameters to **std::forward** them.

* generic lambdas
  * Definition: lambdas that use auto in their parameter specifications
  * Implementation: operator() in the lambda’s closure class is a template.

```c++
auto f = [](auto x){ return func(normalize(x)); };
class SomeCompilerGeneratedClassName {
 public:
	template<typename T>
	auto operator()(T x) const
	{ return func(normalize(x)); }
	...
}

利用reference collapse --->
auto f = [](auto&& x){ return func(normalize(std::forward<decltype(param)>(x))); };

auto f =
  [](auto&&... param){ 
  	return func(normalize(std::forward<decltype(param)...>(x)));
	};
```



##### Item 34: Prefer lambdas to std::bind

* Lambdas are more readable, more expressive, and may be more efficient than using std::bind.

* In C++11 only, `std::bind` may be useful for implementing move capture or for binding objects with templatized function call operators.

lambdas are more readable

lambdas are faster (in some cases, function pointer called through `std::bind` is less likely to be inlined)

```c++
// typedef for a point in time (see Item 9 for syntax)
using Time = std::chrono::steady_clock::time_point;
// see Item 10 for "enum class"
enum class Sound { Beep, Siren, Whistle };
// typedef for a length of time
using Duration = std::chrono::steady_clock::duration;

// at time t, make sound s for duration d
void setAlarm(Time t, Sound s, Duration d);

auto setSoundL =
[](Sound s) {
	// make std::chrono components available w/o qualification
	using namespace std::chrono;
  setAlarm(steady_clock::now() + hours(1),
           s,
           seconds(30));
};

// 错误写法：steady_clock::now()没有在 setAlarm 调用时调用（而是在 std::bind）
using namespace std::chrono;
using namespace std::literals;
using namespace std::placeholders;
auto setSoundB =
  std::bind(setAlarm,
						steady_clock::now() + 1h, // incorrect!
            _1,
						30s);

--->

auto setSoundB =
	std::bind(setAlarm,
						std::bind(std::plus<>(), steady_clock::now(), 1h),
            _1,
						30s);
// C++11: std::plus<steady_clock::time_point>()

--->
// 假如overload setAlarm
void setAlarm(Time t, Sound s, Duration d, Volume v);

using SetAlarm3ParamType = void(*)(Time t, Sound s, Duration d);
auto setSoundB =
	std::bind(static_cast<SetAlarm3ParamType>(setAlarm),
						std::bind(std::plus<>(),
                      steady_clock::now(),
											1h),
            _1,
						30s);


```

```c++
// C++14
auto betweenL =
     [lowVal, highVal]
     (const auto& val)                          
     { return lowVal <= val && val <= highVal; };

using namespace std::placeholders;
auto betweenB =
	std::bind(std::logical_and<>(), // C++14
						std::bind(std::less_equal<>(), lowVal, _1),
            std::bind(std::less_equal<>(), _1, highVal));

// C++11
auto betweenL =
     [lowVal, highVal]
     (int val)                          
     { return lowVal <= val && val <= highVal; };

using namespace std::placeholders;
auto betweenB =
	std::bind(std::logical_and<bool>(), // C++14
						std::bind(std::less_equal<int>(), lowVal, _1),
            std::bind(std::less_equal<int>(), _1, highVal));

```

* `std::bind`: implicitly stored by value
  * `std::bind` stores values, and all arguments passed to bind objects are passed by reference
  * can store refs: `auto compressRateB = std::bind(compress, std::ref(w), _1);`

* Lambdas: explicitly

```c++
enum class CompLevel { Low, Normal, High };
Widget compress(const Widget& w,
                CompLevel lev);
```

* `std::bind`有优势的场景 (all in C++11)
  * Move capture (Item 32)
  * Polymorphic function objects

```c++
class PolyWidget {
public:
 template<typename T>
	void operator()(const T& param);
  ...
};

PolyWidget pw;
auto boundPW = std::bind(pw, _1);
boundPW(1930);
boundPW(nullptr);
boundPW("Rosebud");

// C++14 lambda
auto boundPW = [pw](const auto& param) // C++14
							 { pw(param); };
```

#### chpt 7  The Concurrency API

futures: `std::future` or `std::shared_future`

##### Item 35: Prefer task-based programming to thread-based.

```c++
// thread-based
int doAsyncWork();
std::thread t(doAsyncWork);
// task-based
auto fut = std::async(doAsyncWork);
```

* 优势：返回值；异常容错；脱离 thread 的概念
* thread
  * *Hardware threads* are the threads that actually perform computation. Contemporary machine architectures offer one or more hardware threads per CPU core.
  *  *Software threads* (also known as *OS threads* or *system threads*) are the threads that the operating system manages across all processes and schedules for execution on hardware threads. It’s typically possible to create more software threads than hardware threads, because when a software thread is blocked (e.g., on I/O or waiting for a mutex or condition variable), throughput can be improved by executing other, unblocked, threads.
    * limited resource: 超额申请 -> `std::system_error` (即使函数是noexcept属性)
    * oversubscription: 线程过多 -> context switch 成本、cache 一致性
  * *std::threads* are objects in a C++ process that act as handles to underlying software threads. Some std::thread objects represent “null” handles, i.e., corre‐ spond to no software thread, because they’re in a default-constructed state (hence have no function to execute), have been moved from (the moved-to `std::thread` then acts as the handle to the underlying software thread), have been joined (the function they were to run has finished), or have been detached (the connection between them and their underlying software thread has been severed).
* Task model 脱离 thread 的概念 -> 不用自己做线程管理，交给 runtime scheduler
  * 有全局信息，安排 "run it on the thread needing the result"
  * improve load balancing across hardware cores through work-stealing algorithms
* some situations where using threads directly may be appropriate
  * You need access to the API of the underlying threading implementation.
    * *native_handle*
  * You need to and are able to optimize thread usage for your application.
  * You need to implement threading technology beyond the C++ concurrency API


##### Item 36: Specify std::launch::async if asynchronicity is essential.

* `std::launch::async`: on a different thread
  * GUI thread
* `std::launch::deferred`: deferred until get or wait is invoked
* `default = std::launch::async | std::launch::deferred` 
  * 无法确认是否并行、是否统一线程；可能无法预测是否执行
  * [Async Tasks in C++11: Not Quite There Yet](https://bartoszmilewski.com/2011/10/10/async-tasks-in-c11-not-quite-there-yet/)
    * 与 TLS 互相影响
    * affects wait-based loops using timeouts

```c++
using namespace std::literals;
void f() {
	std::this_thread::sleep_for(1s);
}
auto fut = std::async(f);
while (fut.wait_for(100ms) != std::future_status::ready){
	...
  // loop until f has finished running...
  // which may never happen!
  // fut.wait_for will always return std::future_status::deferred
}
```

->

```c++
auto fut = std::async(f);
if (fut.wait_for(0s) == std::future_status::deferred) {
	// use wait or get on fut to call f synchronously
  ...
} else { // task isn't deferred
	while (fut.wait_for(100ms) != std::future_status::ready) {
    ...
  }
  ...
}
```

```c++
//C++11
template<typename F, typename... Ts>
inline
std::future<typename std::result_of<F(Ts...)>::type>
reallyAsync(F&& f, Ts&&... params) {
  return std::async(std::launch::async,
										std::forward<F>(f),
                    std::forward<Ts>(params)...);
}

//C++14
template<typename F, typename... Ts>
inline auto reallyAsync(F&& f, Ts&&... params) {
  return std::async(std::launch::async,
										std::forward<F>(f),
                    std::forward<Ts>(params)...);
}
```



##### Item 37: Make **std::threads** unjoinable on all paths.

* Joinable `std::thread`
  * Blocked or waiting to be scheduled
  * have run to completion
* Unjoinable `std::thread`
  * Default-constructed std::threads
  * `std::thread` objects that have been moved from. 
  * `std::thread`s that have been joined.
  * `std::thread`s that have been detached.

```c++
constexpr auto tenMillion = 10000000;  
// C++ 14: tenMillion = 10'000'000
bool doWork(std::function<bool(int)> filter,
	          int maxVal = tenMillion) {
	std::vector<int> goodVals;
	std::thread t([&filter, maxVal, &goodVals] {
									for (auto i = 0; i <= maxVal; ++i){
                    if (filter(i)) goodVals.push_back(i);
                  }
	  						});
  // use handle to set t's priority
  // Recommend: start t suspended
  auto nh = t.native_handle();
  ...
  if (conditionsAreSatisfied()) {
    t.join();
    performComputation(goodVals);
    return true;
	}
	return false;
}
```

destruction of a joinable thread causes program termination：以下两种设计都不合理

* An implicit join：
  * 潜藏性能问题
  * Item 39: a hung program ---> interruptible threads ---> Anthony Williams’ *C++ Concurrency in Action* (Manning Publications, 2012), section 9.2.
* An implicit detach：更坏的设计，局部变量销毁

=> 设计 RAII object

* Declare `std::thread` objects last in lists of data members.

```c++
class ThreadRAII {
 public:
	enum class DtorAction { join, detach };
	ThreadRAII(std::thread&& t, DtorAction a)
	: action(a), t(std::move(t)) {}
	~ThreadRAII() {
		if (t.joinable()) {
			if (action == DtorAction::join) {
        t.join();
			} else {
        t.detach();
			}
		}
  }
  ThreadRAII(ThreadRAII&&) = default;
  ThreadRAII& operator=(ThreadRAII&&) = default;
  
  std::thread& get() { return t; }
 
 private:
  DtorAction action;
  std::thread t;
};
```



##### Item 38: Be aware of varying thread handle destructor behavior.

both `std::thread` objects and future objects can be thought of as *handles* to system threads.

* a future is one end of a communications channel through which a callee transmits a result to a caller
  * 信息存在哪？ ---> callee's promise, caller's future 都不行 ---> shared state

* Future destructors normally just destroy the future’s data members.

* The final future referring to a shared state for a non-deferred task launched via `std::async` blocks until the task completes.
  * deferred task <--- an implicit join
  * 另一种产生 shared state 的方式：`std::packaged_task`

```c++
int calcValue();
std::packaged_task<int()> pt(calcValue);
auto fut = pt.get_future();

std::thread t(std::move(pt));

{
  std::packaged_task<int()> pt(calcValue);
	auto fut = pt.get_future();
	std::thread t(std::move(pt));
  ...
}
```



##### Item 39: Consider void futures for one-shot event communication

```c++
std::condition_variable cv;
std::mutex m;

// detect event, tell reacting task
cv.notify_one();

/////////

... //prepare to react
{
  std::unique_lock<std::mutex> lk(m);
  cv.wait(lk); // wait for notify
  ... // react to event
}
...
```

Reacting 代码的问题：

* 可能不必要的 mutex
* If the detecting task notifies the condvar before the reacting task waits, the reacting task will hang.
* The wait statement fails to account for spurious wakeups.

---> `cv.wait(lk, []{ return whether the event has occurred; });`

<=>

```c++
while (!pred()) {
    wait(lock);
}
```

另一种方案

* 缺点是 polling in the reacting task <--- not truly blocked

```c++
std::atomic<bool> flag(false);

flag = true;

...
while (!flag);
...
```

组合方案

```c++
// detector
std::condition_variable cv;
std::mutex m;
bool flag(false);
...
{
	std::lock_guard<std::mutex> g(m);
	flag = true;
}
cv.notify_one();

// reactor
...
{
  std::unique_lock<std::mutex> lk(m);
  cv.wait(lk, [] { return flag; });
}
...
```

组合方案正确性无误，但不简洁

=> having the reacting task wait on a future that’s set by the detecting task (void future)

```c++
std::promise<void> p;

// detector
...
p.set_value();

// reactor
...
p.get_future().wait();
...
```

* 优点：不浪费资源、无 spurious wakeups、无 mutex

* 缺点：incur heap-based allocation and deallocation, limited to one-shot mechanism

e.g.

```c++
std::promise<void> p;
void react();

void detect()
{
  std::thread t([] {
									p.get_future().wait();
									react();
  							});
  ...
  p.set_value();
  ...
  t.join();
}
```

=>

```c++
std::promise<void> p;
void react();

void detect()
{
  ThreadRAII tr(
    std::thread t([] {
                    p.get_future().wait();
                    react();
                  }),
    ThreadRAII::DtorAction::join    // risky!
  );
  
  ... // thread inside tr is suspended here.
      // if an exception emitted --> ThreadRAII never returns
  
  p.set_value(); // unsuspend thread inside tr
  ...
}
```

拓展多个线程

```c++
std::promise<void> p;
void react();

void detect()
{
  auto sf = p.get_future().share();
  std::vector<std::thread> vt;
  
  for (int i = 0; i < threadsToRun; i++) {
    vt.emplace_back([sf]{ sf.wait();
                        	react(); });
  }
  ...
  p.set_value();
  ...
    
  for (auto& t : vt) {
    t.join();
  }
}
```

##### Folly::future

https://github.com/facebook/folly/blob/main/folly/docs/Futures.md

```c++
std::vector<folly::Promise<Input>> pros(inputs.size());
std::vector<folly::Future<Output>> futs;
for (auto& p : pros) {
  auto f = p.getFuture().thenValue([func1](Input input){
      return folly::makeFuture<Output>(func1(input));
    })
    .thenValue([func2](Output output)) {
        return folly::makeFuture<Output>(func2(output));
    }
    .thenValue([func2](Output output)) {
        return folly::makeFuture<Output>(func2(output));
    };
  futs.push_back(std::move(f));
}
auto allf = folly::collectAll(futs);
auto it = ...;
for (auto& p : pros) {
  p.setValue(*it);
  ++it;
}
assert(allf.isReady());
auto& results = allf.value();
```

##### Item 40:  Use **std::atomic** for concurrency, **volatile** for special memory.

`std::atomic` is for data accessed from multiple threads without using mutexes. It’s a tool for writing concurrent software.

* what’s atomic is nothing more than the read of an `std::atomic`
* read-modify-write (RMW) operations

* Data race is an undefined behavior => 变量可能是任意值

* 可用于满足 critical ordering requirement (using sequential consistency)

```c++
std::atomic<bool> valAvailable(false);
auto imptValue = computeImportantValue();
valAvailable = true;
```

* the copy operations for `std::atomic` are deleted
  * 硬件不支持 read x and write y in a single atomic operation
  * Move operations aren't explicitly declared
* `load` and `store`

```c++
std::atomic<int> y(x.load());

y.store(x.load());

x.fetch_add(1, std::memory_order_release);
```

* `exchange`
  * 返回值是旧值
  * `auto pre_val = cur_val_.exchange(cur_val);`
  
* `std::atomic_thread_fence(std::memory_order_release);`

```c++
//Global
std::string computation(int);
void print( std::string );
 
std::atomic<int> arr[3] = { -1, -1, -1 };
std::string data[1000]; //non-atomic data
 
// Thread A, compute 3 values
void ThreadA( int v0, int v1, int v2 )
{
//assert( 0 <= v0, v1, v2 < 1000 );
data[v0] = computation(v0);
data[v1] = computation(v1);
data[v2] = computation(v2);
std::atomic_thread_fence(std::memory_order_release);
std::atomic_store_explicit(&arr[0], v0, std::memory_order_relaxed);
std::atomic_store_explicit(&arr[1], v1, std::memory_order_relaxed);
std::atomic_store_explicit(&arr[2], v2, std::memory_order_relaxed);
}
 
// Thread B, prints between 0 and 3 values already computed.
void ThreadB()
{
int v0 = std::atomic_load_explicit(&arr[0], std::memory_order_relaxed);
int v1 = std::atomic_load_explicit(&arr[1], std::memory_order_relaxed);
int v2 = std::atomic_load_explicit(&arr[2], std::memory_order_relaxed);
std::atomic_thread_fence(std::memory_order_acquire);
// v0, v1, v2 might turn out to be -1, some or all of them.
// otherwise it is safe to read the non-atomic data because of the fences:
if( v0 != -1 ) { print( data[v0] ); }
if( v1 != -1 ) { print( data[v1] ); }
if( v2 != -1 ) { print( data[v2] ); }
}
```



```c++
std::atomic_thread_fence(std::memory_order_release);
version_.fetch_add(1);
```






`volatile` is for memory where reads and writes should not be optimized away. It’s a tool for working with special memory.

* [volatile 关键字本质上是阻止编译器做常量优化](https://www.zhihu.com/question/388121842/answer/1195382979)
* no guarantee of operation atomicity and insufficient restrictions on code reordering
* In a nutshell, it’s for telling compilers that they’re dealing with memory that doesn’t behave normally
* special memory
  * Memory-mapped I/O，与 peripherals 交互
* seemingly redundant loads and dead stores must be preserved when dealing with special memory

共用两个特性：`volatile std::atomic<int> vai`



#### chpt 8 Tweaks

##### Item 41: Consider pass by value for copyable parameters that are cheap to move and always copied.

```c++
class Widget {
 public:
	void addName(std::string newName) { 	
    names.push_back(std::move(newName));
  }
	...
};
```

标题中 copyable 的含义讨论：

```c++
void setPtr(std::unique_ptr<std::string>&& ptr) {
  p = std::move(ptr);
}
```

assignment 场景不同于 construction 的 case：

* applies to any parameter type that holds values in dynamically allocated memory

```c++
class Password {
 public:
	void changeTo(const std::string& newPwd) {
    text = newPwd; // can reuse text's memory if text.capacity() >= new Pwd.size()
  }
}
```

that pass by value is susceptiable to *the slicing problem*

```c++
class Widget { ... };
class SpecialWidget: public Widget { ... };
void processWidget(Widget w); // suffers from slicing problem
SpecialWidget sw;
processWidget(sw);
```



##### Item 42: Consider emplacement instead of insertion

insert, push_front, push_back, `std::forward_list::insert_after`

<->

emplace, emplace_front, emplace_back, `std::forward_list::emplace_after`

* 所有容器中，只有 `std::forward_list`, `std::array` 不支持 `insert`
* [emplace_hint](https://en.cppreference.com/w/cpp/container/map/emplace_hint)

`emplace_back` uses perfect forwarding (limitations -> Item 30)

a heuristic that can help you identify situations where emplacement functions are most likely to be worthwhile

* The value being added is constructed into the container, not assigned.
  * Node-based containers virtually always use construction to add new values, and most standard containers are node-based. The only ones that aren’t are `std::vector`, `std::deque`, and `std::string`. (`std::array` isn’t, either, but it doesn’t support insertion or emplacement, so it’s not relevant here.)
* The argument type(s) being passed differ from the type held by the container.
* The container is unlikely to reject the new value as a duplicate.



two other issues

* `shared_ptr` + `push_back` 异常安全性
  * Fundamentally, the effectiveness of resource-managing classes like `std::shared_ptr` and `std::unique_ptr` is predicated on resources (such as raw pointers from new) being *immediately* passed to constructors for resource-managing objects. The fact that functions like `std::make_shared` and `std::make_unique` automate this is one of the reasons they’re so important.

```c++
std::list<std::shared_ptr<Widget>> ptrs;
void killWidget(Widget* pWidget);
ptrs.push_back(std::shared_ptr<Widget>(new Widget, killWidget));
ptrs.push_back({ new Widget, killWidget });

ptrs.emplace_back(new Widget, killWidget); // 异常安全性问题
```

=>

```c++
std::shared_ptr<Widget> spw(new Widget, killWidget);
ptrs.push_back(std::move(spw));
```

* interaction with `explicit` constructors
  * `emplace_back` is not considered an implicit conversion request
  * 深入思考，direct initialization is permitted to use explicit constructors

```c++
std::vector<std::regex> regexes;
regexes.emplace_back(nullptr); // why is it valid?
regexes.push_back(nullptr); // compile error
--->
std::regex upperCaseWord("[A-Z]+"); // std::regex constructor takeing a const char* pointer is explicit

std::regex r1 = nullptr; // compile error
std::regex r2(nullptr); // compiles
```

### 《More Effective C++》

##### Item 8: Understand the different meanings of new and delete

* the difference between the new operator and operator new
  * new operator: 分配内存 + 初始化对象，含义定死了
    * `string *ps = new string("Memory Management");`
  * operator new: 分配内存
    * `void * operator new(size_t size);`
    * `void *rawMemory = operator new(sizeof(string));`

* [placement new](https://stackoverflow.com/questions/222557/what-uses-are-there-for-placement-new)
  * 自己精细管理内存（析构时需要先手动调用 destructor 再释放内存）
  * 在 shared memory or memory-mapped I/O 场景比较有用

```c++
/***/

class Widget {
  public:
		Widget(int widgetSize);
};

Widget * constructWidgetInBuffer(void *buffer, int widgetSize) {
	return new (buffer) Widget(widgetSize);
}

/***/

typename std::aligned_storage<sizeof(MyData), alignof(MyData)>::type data;
MyData *ptr = new(&data) MyData(2);
```

* `operator new` and `operator delete` is the C++ equivalent of `malloc` and `free` 

* array 形式的 `operator new[]`，会分别为每个 object 做构造和析构

* [Delete this](https://blog.csdn.net/weiwangchao_/article/details/4746969)

* 这个stackoverflow讨论了alignment：https://stackoverflow.com/questions/506518/is-there-any-guarantee-of-alignment-of-address-return-by-cs-new-operation

  * The pointer returned from the allocation function `operator new[]()` is well aligned. But `new T[n]` is not required to, and usually does not, return `operator new[](n * sizeof (T))`. Almost every compiler adds metadata in front to track the number of elements (so that the right number of destructors are called), and sticking a header in front obviously changes the alignment.
    * 通常padding T的size，以确保数组中每个T的内存是对齐的
  * The other thing is that minimal correct alignment which you get from `new[]` is not the same as optimal alignment. For performance reasons you want certain structures aligned to the cache. As such, even if you update your answer to cite the correct section of the Standard, it still doesn't address the question asked. Also, some instructions (notably SSE) *require* more stringent alignment.
  
  * 其实x86下的内存对齐对性能影响不大，不对齐的主要负面作用是：
    * 踩到一些库的坑，比如内存不对齐则走入冷门分支，性能差（e.g. TVM C++ input tensor）
    * 跨平台踩坑，arm主要是atomic指令，要求对齐
  * std的alignment
    * https://en.cppreference.com/w/cpp/language/object#Alignment
    * https://en.cppreference.com/w/cpp/types/max_align_t
    * operator new 的参数 [std::align_val_t](http://en.cppreference.com/w/cpp/memory/new/align_val_t)

### Abseil C++ Tips

#### Tip of the Week #93: using `absl::Span`

*  It provides a read-only interface to the elements of the vector, but it can also be constructed from non-vector types (like arrays and initializer lists) without incurring the cost of copying the elements.
* The caller can pass a slice of the original vector, or pass a plain array. It is also compatible with other array-like containers, like ...
* examples
  * basic usage
  * Safer memcpy
  * Const Correctness for Vector of Pointers

```c++
void TakesVector(const std::vector<int>& ints);
void TakesSpan(absl::Span<const int> ints);

void PassOnlyFirst3Elements() {
  std::vector<int> ints = MakeInts();
  // We need to create a temporary vector, and incur an allocation and a copy.
  TakesVector(std::vector<int>(ints.begin(), ints.begin() + 3));
  // No copy or allocations are made when using Span.
  TakesSpan(absl::Span<const int>(ints.data(), 3));
}

void PassALiteral() {
  // This creates a temporary std::vector<int>.
  TakesVector({1, 2, 3});
  // Span does not need a temporary allocation and copy, so it is faster.
  TakesSpan({1, 2, 3});
}
void IHaveAnArray() {
  int values[10] = ...;
  // Once more, a temporary std::vector<int> is created.
  TakesVector(std::vector<int>(std::begin(values), std::end(values)));
  // Just pass the array. Span detects the size automatically.
  // No copy was made.
  TakesSpan(values);
}
```

```c++
// Good code
class DoThisInstead {
 public:
  absl::Span<const Foo* const> foos() const { return foos_; }

 private:
  std::vector<Foo*> foos_;
};

void Caller(const DoThisInstead& my_class) {
  // This one doesn't compile.
  // my_class.foos()[0]->SomeNonConstOp();
}
```

```c++
absl::Span<float> GetMutableNum(void* ctx) const {
  float* ctx_float = static_cast<float*>(ctx);
  return absl::MakeSpan(ctx_float, ctx_float + dim_size_);
}

auto span = GetMutableNum(ctx);
std::memcpy(span.data(), ...);

absl::Span<const float> a;
auto* mutable_a = const_cast<float*>(a.data());
```



#### Tip of the Week #108: Avoid `std::bind`

* Applying std::bind() to a type you don’t control is always a bug.
* 用 bind_front

#### Use Absl

* https://github.com/abseil/abseil-cpp/blob/master/absl/algorithm/container.h

```c++
template <typename InputSequence, typename OutputIterator>
OutputIterator c_copy(const InputSequence& input, OutputIterator output) {
  return std::copy(container_algorithm_internal::c_begin(input),
                   container_algorithm_internal::c_end(input), output);
}

absl::c_copy(absl::Span<const float>, proto2::RepeatedFieldBackInserter(proto.mutable_num()));
```





### 学习材料

* https://cpppatterns.com/，见[cpp-patterns.cpp]

* [大神 Andrei Alexandrescu 的 ppt，讲C语言优化](https://www.slideshare.net/andreialexandrescu1/three-optimization-tips-for-c-15708507)
* https://github.com/miloyip/itoa-benchmark/

#### [GoingNative 2013 C++ Seasoning](https://www.youtube.com/watch?v=W2tWOdzgXHA)

3 Goals for Better Code

* No Raw Loops
  * 问题：raw loop 影响对上下文理解、隐藏内部性能问题
  * 解决：STL functions
    * Now we can have the conversation about supporting multiple selections and disjoint selections!
  * Range based for loops for for-each and simple transforms
    * Use const auto& for for-each and auto& for transforms
    * Keep the body **short**
      * A general guideline is no longer than composition of two functions with an operator

```c++
template <typename I> // I models RandomAccessIterator
auto slide(I f, I l, I p) -> pair<I, I>
// 将 [f,l]上滑到 p 或 下滑到 p
{
    if (p < f) return { p, rotate(p, f, l) };
    if (l < p) return { rotate(f, l, p), p };
    return { f, l };
}


template <typename I, // I models BidirectionalIterator
          typename S> // S models UnaryPredicate
auto gather(I f, I l, I p, S s) -> pair<I, I> 
{
	return { stable_partition(f, p, not1(s)), stable_partition(p, l, s) };
}
```

```c++
// Next, check if the panel has moved to the left side of another panel.
auto f = begin(expanded_panels_) + fixed_index;
auto p = lower_bound(begin(expanded_panels_), f, center_x,
[](const ref_ptr<Panel>& e, int x){ return e->cur_panel_center() < x; }); // If it has, then we reorder the panels.
rotate(p, f, f + 1);
```

* No Raw Synchronization Primitives
  * Synchronization primitives are basic constructs such as: Mutex、Atomic、Semaphore、Memory Fence
  * [Amdahl's Law]([https://en.wikipedia.org/wiki/Amdahl%27s_law](https://en.wikipedia.org/wiki/Amdahl's_law)): 并行优化scaling特性取决于程序的异步、同步模型
  * Task Systems: object, thread pool
  * Unfortunately, we don’t yet have a standard async task model, `std::async()` is currently defined to be based on threads
    * This may change in C++14 and Visual C++ 2012 already implements std::async() as a task model
    * Windows - Window #read Pool and PPL
    * Apple - Grand Central Dispatch (libdispatch): Open sourced, runs on Linux and Android
    * Intel TBB - many platform
  * std::packaged_task can be used to marshall results, including exceptions, from tasks
    * `std::packaged_task` is also useful to safely bridge C++ code with exceptions to C code
    * see prior `async()` implementation for an example


```c++
template <typename T>
class bad_cow {
	struct object_t {
		explicit object_t(const T& x) : data_m(x) { ++count_m; }
		atomic<int> count_m;
		T data_m;
	};
	object_t* object_m;
  public:
	explicit bad_cow(const T& x) : object_m(new object_t(x)) { }
	~bad_cow() { if (0 == --object_m->count_m) delete object_m; }
	bad_cow(const bad_cow& x) : object_m(x.object_m) { ++object_m->count_m; }
	bad_cow& operator=(const T& x) {
		if (object_m->count_m == 1) object_m->data_m = x; 
		else {
			object_t* tmp = new object_t(x);
			// --object_m->count_m;
      // =>
      // if (0 == --object_m->count_m) delete object_m;
			object_m = tmp;
		}
    return *this;
  }
};
```

```c++
// C++14 compatible async with libdispatch
namespace adobe {
template <typename F, typename ...Args>
auto async(F&& f, Args&&... args)
				-> std::future<typename std::result_of<F (Args...)>::type>
{
  using result_type = typename std::result_of<F (Args...)>::type;
	using packaged_type = std::packaged_task<result_type ()>;
	auto p = new packaged_type(std::forward<F>(f), std::forward<Args>(args)...);
  auto result = p->get_future();
  dispatch_async_f(dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT, 0), p, [](void* f_) {
		packaged_type* f = static_cast<packaged_type*>(f_); (*f)();
		delete f;
	});
    return result;
}
  
} // namespace adobe
```

```c++
// std::list can be used in a pinch to create thread safe data structures with splice
template <typename T> class concurrent_queue
{
	mutex   mutex_;
  list<T> q_;
 public:
  void enqueue(T x) {
    list<T> tmp;
		tmp.push_back(move(x));
		{
			lock_guard<mutex> lock(mutex); 
      q_.splice(end(q_), tmp);
		} 
  }
	// ...
};
```

* No Raw Pointers

  Why Raw Pointers

  * For containers we’ve moved from intrusive to non-intrusive (STL) containers
    * Except for hierarchies - but containment hierarchies or non-intrusive hierarchies are both viable options
    * [intrusive vs nontrusive](https://www.boost.org/doc/libs/1_35_0/doc/html/intrusive/intrusive_vs_nontrusive.html)
  * PIMPL and copy optimizations are trivially wrapped
  * See previous section regarding shared storage for asynchronous operations
  * Runtime polymorphism

  用智能指针处理的defects：1）要注意异常安全性=>make_shared；2）改变了对象的 semantics of copy, assignment and equality；3）thread-safety concerns

  * shared structure also breaks our ability to reason locally about the code

```c++
class my_class_t : public object_t
{
public:
  void draw(ostream& out, size_t position) const {
    out << string(position, ' ') << "my_class_t" << endl; 
  } 
  /* ... */
};
int main() {
	document_t document;
	document.emplace_back(new my_class_t());
  draw(document, cout, 0);
}

======> 用封装防范两个函数修改同一个object

template <typename T>
void draw(const T& x, ostream& out, size_t position) {
  out << string(position, ' ') << x << endl; 
}
class object_t {
 public:
	template <typename T> // T models Drawable
  // Pass sink arguments by value and move into place
	object_t(T x) : self_(make_shared<model<T>>(move(x))) { }
	friend void draw(const object_t& x, ostream& out, size_t position) {
    x.self_->draw_(out, position); 
  }

 private:
  struct concept_t {
		virtual ~concept_t() = default;
		virtual void draw_(ostream&, size_t) const = 0; 
  };
	template <typename T> struct model : concept_t {
		model(T x) : data_(move(x)) { }
		void draw_(ostream& out, size_t position) const { 
      draw(data_, out, position); 
    }
		T data_; 
  };
  shared_ptr<const concept_t> self_; 
};
using document_t = vector<object_t>;
void draw(const document_t& x, ostream& out, size_t position)
{
    out << string(position, ' ') << "<document>" << endl;
    for (auto& e : x) draw(e, out, position + 2);
    out << string(position, ' ') << "</document>" << endl;
}

class my_class_t // 无需继承 object_t => my_class_t 可以同时满足多个 polymorphic settings
{
 public:
  void draw(ostream& out, size_t position){ 
  	out << string(position, ' ') << "my_class_t" << endl;
	}
};

int main(){
	document_t document;
	document.emplace_back(my_class_t());
  auto saving = async([=]() { 
    this_thread::sleep_for(chrono::seconds(3));
    cout << "-- save --" << endl;
    draw(document, cout, 0);
	});
  document.emplace_back(document);
  
  draw(document, cout, 0);
  saving.get();
}
```


#### 性能友好的 C++ 代码 by 张青山

* Static 修饰很关键，告诉编译器变量的可见范围在当前编译单元
  * const 没有意义，因为可以 [const_cast](https://stackoverflow.com/questions/7311041/const-to-non-const-conversion-in-c)
  * 也可以打包在结构体栈对象里面，全文传递
* `std::string_view` v.s. `std::string`
  * 编译器会有一个编译单元，生成唯一的构造函数，专门初始化所有全局对象

* 普通容器的构造函数通常在cpp文件内定义，编译器无法分析是否有副作用（修改全局变量、操作设备等），所以即使没人使用它们，也需要构造出来
* 不要在头文件中定义容器对象【非 POD(plain old data) 数据】
  * 任何 include "xxx.h" 所编译出来的.o 文件里面都会创建这些对象，也就是说链接出来的二进制中有很多份对象
    * 之所以不得不创建，本质上是因为非POD数据有构造函数，需要动态分配内存，编译器不敢做优化
    * 非要这样做，可以考虑用 extern
  * C++标准在推更多 [constexpr容器](http://www.open-std.org/jtc1/sc22/wg21/docs/papers/2019/p0784r7.html)
  * Guideline: 能用array用array，放在头文件定义；不能用array的，放在cpp定义

```c++
"def.h"
#ifndef MAP
#define MAP(x, y)
#endif
MAP(HELLO, 4)
MAP(WORLD, 6)
...
#undef MAP
  
"header.h"
const std::unordered_map<std::string, int> map = {
#define MAP(x, y) {#x, y},
#include "xxx.def"
};

const std::vector<int> vec = {
#define MAP(x, y) y,
#include "xxx.def"
};
```

##### ANSI aliasing

* 对 cast 完的指针做 dereference 是个 UB(Undefined Behavior) 行为
* strict-aliasing
  * TBAA(type based alias analysis): 编译器假设不同类型指针指向的内存是不交叉的
    * O2以上默认开启
  * 本质上，要保证指针在生产和消费时的类型是一致的
  * 注意：alias 排除 void * 和char *，可以随便 cast 他们，是为了给比如 `int *p = (int*)malloc(sizeof(int));` 留后门
* uint8_t 的 strict aliasing 讨论：https://stackoverflow.com/questions/26297571/how-to-create-an-uint8-t-array-that-does-not-undermine-strict-aliasing
  * [Is `uint8_t` always an alias for a character type if it exists?](https://software.codidact.com/posts/280966)
  * [关于 bytes 的讨论](https://gist.github.com/jibsen/da6be27cde4d526ee564), 需要看 CHAR_BIT 是否等于 8（通常是的），所以认为 uint8_t 等同于 unsigned char
* **-fno-strict-aliasing** 来禁掉该优化，但如果关掉 strict-aliasing, 对程序的性能有巨大的影响



* 慎用 C++ 异常

  * 发生异常会两次回溯整个调用栈，代价非常大，不要用来解决控制流切换
  * 对编译器的影响：1）eh_frame 生成数据，影响代码 size；2）插入代码，影响 icache
  * -fno-exceptions
* 短函数尽量在头文件实现

  * 如果声明和实现分离，编译器不知道实现里做了什么
  * 可以用 LTO 优化来解决

```c++
// "a.h"
struct A() {
  A();
  int buf[1000];
}

int main() {
  A a;  // 不会优化成空语句
  return 0;
}

// "a.cpp"
A::A() {}
```

* 循环条件外提
  * 这里编译器每次都会算 m.end()
  * range base for 假设循环不修改容器

```c++
void bar();
int foo(const std::vector<int>& m) {
  int sum = 1;
  for (auto it = m.begin(); it != m.end(); it++) {
    bar();
    sum += *it;
  }
  return sum;
}
```

### Potpourri

#### 编码规范

* RAII原则：Resource acquisition is initialization，充分利用局部对象的构造和析构特效，常需要与 rule of five, rule of zero 结合

* [Google C++ Style](https://google.github.io/styleguide/cppguide.html)
* [Google: Developer Documentation Style Guide](https://developers.google.com/style)
* [CppCoreGuidelines](https://github.com/isocpp/CppCoreGuidelines/blob/master/CppCoreGuidelines.md)
* 用[CppCheck](http://cppcheck.net/)诊断，`make cppcheck`

* format
  * `/llvm-6.0/bin/clang-format -i *.cpp`

* rules
  * ["explicit" should be used on single-parameter constructors and conversion operators](https://rules.sonarsource.com/cpp/RSPEC-1709)
* 经典案例
  * [goto fail](https://coolshell.cn/articles/11112.html)



#### Debug

* 参考我的 [Debugging and Profiling笔记]()

#### 编译相关

* 参考我的 [Compiler笔记]()



#### C

STDERR_FILENO: [文件描述符的概念](http://guoshaoguang.com/blog/tag/stderr_fileno/)

volatile特性：这条代码不要被编译器优化，`volatile int counter = 0`，避免出现意料之外的情况，常用于全局变量

C不能用for(int i=0; ; ) 需要先定义i

负数取余是负数，如果想取模：a = (b%m+m)%m;

Dijkstra反对goto的[文章](http://www.cs.utexas.edu/users/EWD/ewd02xx/EWD215.PDF)

getopt函数处理参数，用法参照[tsh.c](https://github.com/huangrt01/CSAPP-Labs/blob/master/shlab-handout/tsh.c)

##### 基本数据类型

* 空张量的 reduce 行为（TF/PyTorch）：reduce_max 返回 -inf，reduce_min 返回 +inf
  * 本质是幺半群单位元：max 的单位元是 -∞，min 的单位元是 +∞，空集 reduce 只能返回单位元
  * 同理：空集 sum = 0，空集 prod = 1
  * 工程意义：filter 后可能得到空 tensor，若未处理 reduce 结果会导致下游 NaN（如除以 -inf）
  * 详见 [Mathematics.md - 空集的极值与单位元](./Mathematics.md#基础运算)
* IEEE 754 浮点数 NaN 传播规则：$$0 \times \infty = \text{NaN}$$
  * 设计动机：0 表示"零值或未初始化"，∞ 表示"溢出或无界"，两者语义矛盾——无法确定结果是 0 还是 ∞，因此标记为 NaN（不确定）
  * NaN 传播：任何与 NaN 的算术运算结果仍为 NaN，确保异常信号不被静默吞掉
  * 其他产生 NaN 的典型场景：$$\infty - \infty$$、$$0 / 0$$、$$\sqrt{-1}$$

```c
"/usr/include/stdint.h"
/* Types for `void *' pointers.  */
#if __WORDSIZE == 64
# ifndef __intptr_t_defined
typedef long int		intptr_t;
#  define __intptr_t_defined
# endif
typedef unsigned long int	uintptr_t;
#else
# ifndef __intptr_t_defined
typedef int			intptr_t;
#  define __intptr_t_defined
# endif
typedef unsigned int		uintptr_t;
#endif
```


##### 运算优先级

经典例子：`x = a + b & c`，加法更优先


##### 结构体

* 结构体局部变量要初始化（天坑......）
* 结构体内存分配问题：[内存对齐](https://www.cnblogs.com/zyk1113/p/14356984.html)
  * 起始地址为该变量的类型所占的整数倍，若不足则不足部分用数据填充至所占内存的整数倍。
  * 该结构体所占内存为结构体成员变量中最大数据类型的整数倍。
  * e.g.: 1+4+1+8->4+4+8+8=24
  * 基于内存对齐特性，可以有一些巧妙的设计，利用上对齐的额外空间，增加新属性而不增加内存
  * 属性设置
    * 字节对齐：`__attribute__ ((__packed__))`
* [Bit-field in structures](https://leavinel.blogspot.com/2012/06/bit-field-in-structures.html)

##### switch语句

* case后面加 {}，否则后面case中会有未定义的局部变量
  * https://stackoverflow.com/questions/5685471/error-jump-to-case-label-in-switch-statement
* 要将Enum类型转化为int
  * https://stackoverflow.com/questions/11076941/warning-case-not-evaluated-in-enumerated-type


##### 宏

[C++宏编程，不错的一篇blog](http://notes.tanchuanqi.com/language/cpp/cpp_micro.html)

* `__VA_ARGS__` 

```c++
#define LOGF_AND_PRINT(...) \
  printf(__VA_ARGS__);      \
  printf("\n");             \
  LOGF_ERROR(__VA_ARGS__)   \
  
  auto A = (__VA_ARGS__);
```

* do while(0) 技巧
  * 宏中可使用局部变量

* roundup

```c++
block_size = roundup(block_size, ::sysconf(_SC_PAGESIZE));  // 4KB
```

* Note
  * C 的预处理程序也可能引起某些意想不到的结果。例如，宏UINT_MAX 定义在limit.h中，但假如在程序中忘了include 这个头文件，下面的伪指令就会无声无息地失败，因为预处理程序会把预定义的UINT_MAX 替换成0：

```c++
#if UINT_MAX > 65535u
......
#endif
```



##### 大小端

Big-Endian和Little-Endian的定义如下：

1) Little-Endian就是低位字节排放在内存的低地址端，高位字节排放在内存的高地址端

2) Big-Endian就是高位字节排放在内存的低地址端，低位字节排放在内存的高地址端（和字符串相似）

```c++
// 不同机器，统一返回小端
inline uint64_t native_to_little(uint64_t in) {
    const static union {
        uint32_t i;
        char c[4];
    } endian_test = {0x01000000};

    switch(endian_test.c[0]) {
        case 1:
            in = ((in >> 32) & 0x00000000FFFFFFFFULL) |
                 ((in << 32) & 0xFFFFFFFF00000000ULL);
            in = ((in >> 16) & 0x0000FFFF0000FFFFULL) |
                 ((in << 16) & 0xFFFF0000FFFF0000ULL);
            in = ((in >> 8) & 0x00FF00FF00FF00FFULL) |
                 ((in << 8) & 0xFF00FF00FF00FF00ULL);
        default:
            break;
    }
    return in;
}
```








#### C++的特性
面向对象、构造函数、析构函数、动态绑定、内存管理

* 从`int *p=(int *)malloc(sizeof(int));`到`int *p=new int[10]`
* 二维数组的定义：`TYPE(*p)[N] = new TYPE[][N];`，要指出行数
* 复制构造函数：常引用
* 析构函数
  * 对象的 destructor 不被 call 的情形：Most stem from abnormal program termination. If an exception propagates out of a thread’s primary function (e.g., main, for the program’s initial thread) or if a noexcept specification is violated (see Item 14), local objects may not be destroyed, and if `std::abort` or an exit function (i.e., `std::_Exit`, `std::exit`, or `std::quick_exit`) is called, they definitely won’t be.
* 虚函数   =>对象内有虚函数表，指向虚函数表的指针：32位系统4字节，64位系统8字节
  * 虚析构函数
* 虚基类偏移量表指针



##### static

* 总览
  * https://stackoverflow.com/questions/6223355/static-variables-in-member-functions
  * When used for data members it means that the data is **allocated in the class** and not in instances.
  * When used for data inside a function it means that the data is allocated statically, **initialized the first time the block is entered** and lasts until the program quits. Also the variable is visible only inside the function. This special feature of local statics is often used to implement lazy construction of singletons.
  * When used at a compilation unit level (module) it means that the variable is like a global (i.e. allocated and initialized before `main` is run and destroyed after `main` exits) but that **the variable will not be accessible or visible in other compilation units**.

* [Why can't I initialize non-const static member or static array in class?](https://stackoverflow.com/questions/9656941/why-cant-i-initialize-non-const-static-member-or-static-array-in-class)

```c++
class Class {
public:
    static std::vector<int> & replacement_for_initialized_static_non_const_variable() {
        static std::vector<int> Static {42, 0, 1900, 1998};
        return Static;
    }
};
```

* [thread-safe initialization of local static objects](https://www.eevblog.com/forum/programming/what-is-thread-safe-initialization-of-local-static-objects/)
  * C++11起



##### using / namespace

https://www.runoob.com/cplusplus/cpp-namespaces.html

```c++
namespace XXX{
	//
}
using namespace XXX;
using XXX::object;

//可嵌套
using namespace namespace_name1::namespace_name2;
```

* 匿名命名空间：写在cpp文件里
  * 编译器在内部会为这个命名空间生成一个唯一的名字，而且还会为这个匿名的命名空间生成一条using指令
  * 具有internal属性，不会被外部文件声明extern链接
  * 不要在头文件中使用匿名命名空间，提倡在cpp/cc文件中使用匿名命名空间来代替static关键字。
    * 会在每个引用他的cpp文件中生成大量数据

* [派生类中使用 using::父类::函数名](https://blog.csdn.net/qq_33154343/article/details/101381793)
  * “隐藏”是指派生类的函数屏蔽了与其同名的基类函数，规则如下：
    * 如果派生类的函数与基类的函数同名，但是参数不同。此时，不论有无virtual关键字，基类的函数将被隐藏（注意别与重载混淆）。
    * 如果派生类的函数与基类的函数同名，并且参数也相同，但是基类函数没有virtual关键字。此时，基类的函数被隐藏（注意别与覆盖混淆）



##### std::function

编程模式

* 减少重复代码（避免用宏）

```c++
void object_loop(const std::function<void(Object&)>& func) {
  for (auto& input : inputs) {
  	func(input);
  }
}

void do_sth() {
  object_loop([&](Object& input) {
    if (is_valid(input)) {
      process(input);
    }
  });
}
```

* 线程池使用

```c++
auto func = [&](int tid, size_t mi) {
  process_part(mi);
};
my_thread_pool()->parallel_for(parallel_num, begin, end, func);
```

##### range iteration
```c++
int arr[] = {1, 2, 3, 4, 5};
for (int value : arr) {
// Use value
}
std::vector<int> vec = {1, 2, 3, 4, 5};
for (int& ref : vec) {
// Modify ref
}
```

It supports arrays, types that provide begin and end member functions, and types for which begin and end functions are found via argument-dependent lookup

##### [RTTI (Run-Time Type Information)](https://en.wikibooks.org/wiki/C%2B%2B_Programming/RTTI)

* dynamic_cast
  * 会返回nullptr
* typeid
  * `const std::type_info& info = typeid(object_expression);`
  * does not support reference types.

##### constexpr if

https://en.cppreference.com/w/cpp/language/if#Constexpr_if

```c++
template<typename T>
auto get_value(T t)
{
    if constexpr (std::is_pointer_v<T>)
        return *t; // deduces return type to int for T = int*
    else
        return t;  // deduces return type to int for T = int
}

std::is_same<T, MyType>::value
```





#### 操作符重载
**特点**
* 既不能改变原运算符的运算优先级和结合性，也不能改变操作数的个数
  * *“.”、“.*”(成员指针运算符)、“::”（作用域分辨符）、“ ? : ”（三目运算符） 、sizeof 以及typeid这6个操作符不能重载。否则会带来难以琢磨的问题

* 和类的概念紧密联系，操作数中至少有一个是自定义的类类型。 这一点也和编译原理有联系

**成员函数和友元函数**

* 非成员函数不一定要作为类的友元，如果只通过外部接口访问类，当类的内部结构改变时，不用改操作符
```c++
inline WrappingInt32 operator++(WrappingInt32 &a, int) {
    uint32_t r = a.raw_value();
    a = a + 1;
    return WrappingInt32(r);
}
```

* `=, [], (), ->`只能重载为成员函数
* 友元函数实现
```c++
#include <iostream>
using namespace std;
class pwr {
public: 
	pwr(int i) { num = i; }
	friend int operator ^(pwr, pwr);
private: int num;
};
int operator ^(pwr b, pwr e)
{
	int t, temp;
	temp = b.num;
	for (t = e.num - 1; t; t--)
		b.num *= temp;
	return b.num;
}
```

* 二目操作符的成员函数：参数常引用

`bool operator==(const Operation& other) const { return node_ == other.node_; }`

* 二目操作符的友员函数
* 单目操作符的成员函数
  * 前置重载`++a`视为无形参的成员函数，后置`a++`具有一个int类型形参
  * 前置重载`++a`返回值带引用，而后置重载返回值不带引用
* 单目操作符的友元函数：见上面`WrappingInt32`的例子

**其它操作符重载**

1.string类的赋值运算符函数
* 经典解法：考虑[返回引用](https://bbs.csdn.net/topics/100000589?depth_1-utm_source=distribute.pc_relevant.none-task&utm_source=distribute.pc_relevant.none-task)、连续赋值、等号两边相同的情形
```c++
CMyString& CMyString::operator=(const CMyString &str){
	if(this==&str)
		return *this;
	delete []m_pData;
	m_pData = new char[strlen(str.m_pData)+1];
	strcpy(m_pData, str.m_pData);
	return *this;
}
```
* 考虑异常安全性：上面的解法在 new 分配之前先 delete，违背了 Exception Safety 原则，我们需要保证分配内存失败时原先的实例不会被修改，因此可以先复制，或者创造临时实例。(临时实例利用了if语句，在if的大括号外会自动析构)
```c++
CMyString& CMyString::operator=(const CMyString &str){
	if(this!=&str){
		CMyString strTemp(str);
		swap(m_pData,strTemp.m_pData);
	}
	return this;
}
```

2.<< 操作符的重载
* `ostream &operator << (ostream &output, 自定义类型&); //istream也可`
* 只能重载为类的友元函数（否则必须修改系统的ostream类，不被允许） 
* 为了级联输出，重载函数的形参和返回值必须是I / O对象的引用
* 对于 `cout << c1 << c2 << c3;`语句，编译器需要一次性生成可执行代码，因为C++是编译型语言，不是BASIC那种边编译边执行的解释型语言。为了按照c1，c2，c3的顺序输出，就需要把对象按照c3，c2，c1的次序依此入栈，便于执行时的边出栈边打印，因此一次性传递完参数然后再从左向右执行。

3.类型操作符的重载强制类型转换

```c++
operator 类型名()
{
	return 与类型名类型相同的转换结果;
}
```

* 此函数前没有返回类型，函数也没有参数。函数将会自动返回与类型转换函数类型名相同的类型。
* 这里的类型名是基本数据类型int，double等。
* 类型转换函数只能作为相应类的成员函数。
* 总的来看，类中的类型转换函数优先级很高，导致类的对象在运算时，不按常规方式操作，而是先进行类型强制转换，导致结果不可琢磨，因此类型转换函数要慎用！

#### 继承与派生

[Access Modifiers in C++](https://www.geeksforgeeks.org/access-modifiers-in-c/)

* protected: 类似private，但可以被派生类调用

派生类的ctor要指明基类对象的初始化方式（否则用基类的无参构造函数）

```c++
class SpecialPerson: public Person {
public:
	SpecialPerson(const SpecialPerson& rhs) : Person(rhs) {... }
	SpecialPerson(SpecialPerson&& rhs) : Person(std::move(rhs)) {... }
};
```

#### 模版

* Basics
  * 在C++中，模板函数的定义和声明必须在同一个翻译单元中（通常是一个源文件）。原因在于模板是编译期生成代码的，它们在实例化时需要可见其定义。如果仅在头文件中声明模板函数而不定义，会导致链接错误（例如undefined symbol错误）。
    * 方案一：将定义放在头文件中
    * 方案二：定义放在源文件中，头文件中显式实例化

* 模板编程中使用`auto`作为函数参数类型

```c++
#include <iostream>
#include <string>
#include <type_traits>

template <typename F>
void execute(F func) {
    func();
}

int main() {
    auto void_func = [&](const std::string& name, auto value) {
        std::cout << "Name: " << name << ", Value: " << value << std::endl;
    };

    execute([&]() { void_func("Age", 30); });
    execute([&]() { void_func("Height", 5.9); });
    execute([&]() { void_func("IsStudent", true); });

    return 0;
}

auto int_func = [](auto value) {
    static_assert(std::is_integral<decltype(value)>::value, "Only integral types are allowed");
    std::cout << "Value: " << value << std::endl;
};
```





#### C++的其它可扩展性

* [类的成员指针函数](https://www.cnblogs.com/zhoug2020/p/11394408.html)
```c++
class Solution;
typedef bool (Solution::*FP_func)(int n);
class Solution {
public:
    FP_func m_pfn_func;
    bool isEven(int n){
        return (n&1)==0;
    }
    vector<int> exchange(vector<int>& nums) {
        m_pfn_func=&Solution::isEven;
        if(nums.empty())return nums;
        int i=-1,j=nums.size();
        while(1){
            while(!(this->*m_pfn_func(nums[++i]))if(i==nums.size()-1)break;
            while((this->*m_pfn_func)(nums[--j])) if(j==0)break;
            if(i>=j)break;
            swap(nums[i],nums[j]);
        }
        return nums;
    }
};
```
* 类的静态成员函数指针



#### 输入输出

##### 文件

* [Read_file_to_string](https://www.delftstack.com/howto/cpp/read-file-into-string-cpp/)
  * istreambuf_iterator
  * rdbuf

```c++
static std::string read_file(const std::string& file_name) {
  std::string str = "";
  std::ifstream infile;
  infile.open(file_name);
  infile.seekg(0, std::ios::end);
  str.reserve(infile.tellg());
  infile.seekg(0, std::ios::beg);

  str.assign((std::istreambuf_iterator<char>(infile)),
              std::istreambuf_iterator<char>());
  infile.close();
  return str;
}
```

* 关于linux阻塞/非阻塞读
  * 返回非零值：实际read到的字节数
  * 返回-1
    * errno != EAGAIN (或!= EWOULDBLOCK) read 出错
    * errno == EAGAIN (或== EWOULDBLOCK) 设置了非阻塞读，并且没有数据到达
  * 返回0：读到文件末尾
  * 工程实践
    * cs144/sponge 的 eventloop 设计



##### 输入用逗号间隔的数据

* 方法一：[混合使用cin>>和cin.get()](http://c.biancheng.net/view/1346.html)
* 方法二：利用string和strtok
```c++
class cplus_input{
    public:
        vector<int> num;
        void input_comma(){
            int a;
            while (cin >> a)
            {
                num.push_back(a);
                if (cin.get() == '\n')
                    break;
            }

            // string s;
            // cin >> s;
            // char *str = (char *)s.c_str(); //string --> char
            // const char *split = ",";
            // char *p = strtok(str, split); //逗号分隔依次取出
            
            // while (p != NULL)
            // {
            //     sscanf(p, "%d", &a); //char ---> int
            //     num.push_back(a);
            //     p = strtok(NULL, split); //s为空值NULL，则函数保存的指针SAVE_PTR在下一次调用中将作为起始位置。
            // }
            return;
        }
};


```



LOG代码

* `#、__FILE__、__LINE__` 的运用

```c++
#define CHECK(x)                                                \
  if (!(x))                                                       \
  LogMessageFatal(__FILE__, __LINE__).stream() \
      << "Check failed: " #x << ": "

namespace euclid {
namespace rosetta {

class LogMessageFatal {
 public:
  LogMessageFatal(const char* file, int line) {
    log_stream_ << file << ":" << line << ": ";
  }
  std::ostringstream& stream() {
    return log_stream_;
  }
  ~LogMessageFatal() noexcept(false) {
    throw std::runtime_error(log_stream_.str());
  }

 private:
  std::ostringstream log_stream_;
};
```

* `__VA_ARGS__` 的[应用](https://stackoverflow.com/questions/26053959/what-does-va-args-in-a-macro-mean)



#### multi-thread programming

* 读写锁
  * unique_lock和lock_guard的区别
    * 是否可move
    * 是否可和条件变量配合

  * [A shared recursive mutex in standard C++](https://stackoverflow.com/questions/36619715/a-shared-recursive-mutex-in-standard-c)
    
  * Note: [mutex 和 cv 都没有移动构造函数](https://stackoverflow.com/questions/7557179/move-constructor-for-stdmutex)


```c++
#include <boost/thread/thread.hpp>
#include <shared_mutex>

//读锁
//灵活使用：用{}包起来，控制释放锁的时机
{
	std::shared_lock<boost::shared_mutex> lock(mutex_);
}

//写锁
std::unique_lock<boost::shared_mutex> lock(mutex_);

lock.unlock(); //临时解锁
// do sth
lock.lock(); //继续上锁
// do sth
```

* 自旋锁 (spinlock)
  * [single bit spinlock](https://news.ycombinator.com/item?id=21930374)
    * [How do I choose between the strong and weak versions of compare-exchange?](https://devblogs.microsoft.com/oldnewthing/20180330-00/?p=98395)
  * [Correctly implementing a spinlock in C++](https://rigtorp.se/spinlock/#fn:2)
    * Test and test-and-set (TTAS) lock
    * pause的意义，也可以用 [folly::detail::sleeper](https://github.com/facebook/folly/blob/main/folly/synchronization/detail/Sleeper.h)

```c++
auto old = addr.load(std::memory_order_relaxed);
while(not addr.compare_exchange_weak(old, old|1)) {};


std::atomic<Widget*> cachedWidget;

Widget* GetSingletonWidget()
{
 Widget* widget = cachedWidget;
 if (!widget) {
  widget = new(std::nothrow) Widget();
  if (widget) {
   Widget* previousWidget = nullptr;
   if (!cachedWidget.compare_exchange_strong(previousWidget, widget)) {
    // lost the race - destroy the redundant widget
    delete widget;
    widget = previousWidget;
   }
  }
 }
 return widget;
}
```

```c++
struct ttas_lock {
  ...
  void lock() {
    for (;;) {
      if (!lock_.exchange(true, std::memory_order_acquire)) {
        break;
      }
      while (lock_.load(std::memory_order_relaxed)) {
        __builtin_ia32_pause();
      }
    }
  }
  ...
};

struct spinlock {
  std::atomic<bool> lock_ = {0};

  void lock() noexcept {
    for (;;) {
      // Optimistically assume the lock is free on the first try
      if (!lock_.exchange(true, std::memory_order_acquire)) {
        return;
      }
      // Wait for lock to be released without generating cache misses
      while (lock_.load(std::memory_order_relaxed)) {
        // Issue X86 PAUSE or ARM YIELD instruction to reduce contention between
        // hyper-threads
        __builtin_ia32_pause();
      }
    }
  }

  bool try_lock() noexcept {
    // First do a relaxed load to check if lock is free in order to prevent
    // unnecessary cache misses if someone does while(!try_lock())
    return !lock_.load(std::memory_order_relaxed) &&
           !lock_.exchange(true, std::memory_order_acquire);
  }

  void unlock() noexcept {
    lock_.store(false, std::memory_order_release);
  }
};
```

* std::atomic

```c++
// 让并发函数中的某一global部分不并发
bool cur = false;
if (updating_.compare_exchange_weak(cur,true)) {
  if (timer_ptr_->tick()) {
    update();
  }
  updating_.store(false);
}
```





* 大量读，少量更新，可以用`tbb::concurrent_hash_map<key_type, value_type>;`

```c++
{
	typename map_type::const_accessor cit;
	bool found = _map.find(cit, key);
}
{
  typename map_type::accessor it;
  _map.insert(it, key);
}

using queue_type = tbb::concurrent_bounded_queue<timed_key>;
_queue.try_push(tk);
while(_queue.try_pop(tk)){
  ...
}
```

* ThreadPool
  * [Thread pool that binds tasks for a given ID to the same thread](https://stackoverflow.com/questions/8162332/thread-pool-that-binds-tasks-for-a-given-id-to-the-same-thread)
  * C++ 有什么好用的线程池？ - neverchanje的回答 - 知乎 https://www.zhihu.com/question/397916107/answer/1253114248
  * [Uneven Work Distribution and Oversubscription](https://dzone.com/articles/uneven-work-distribution-and)
  * 一些坑：
    * 同一线程池执行的任务不能有依赖关系，否则可能pending
* MemoryPool
  * [C++ Memory Pool and Small Object Allocator](https://betterprogramming.pub/c-memory-pool-and-small-object-allocator-8f27671bd9ee)
    * Small-Object Allocation is likely to cause fragmentation
    * Boost Singleton Pool:
      * When a block is fully used, the Singleton Pool will *automatically* add a new block by doubling the size
* 条件变量

```c++
std::mutex mu;
std::condition_variable cv;

cv.notify_one();
cv.notify_all();

void wait_task() {
  std::unique_lock<std::mutex> lk(mu);
  cv.wait(lk, [this]() { return ready; });
}

void finish_task() {
  std::unique_lock<std::mutex> lk(mu);
  ready = true;
  cv.notify_one();
}
```

* Shared Store

  * 参考 `shared_store.h`
  * `SharedStore<ObjectPool>` 常见用法
* Thread Local
  * [C++11 thread_local用法](https://zhuanlan.zhihu.com/p/340201634) : `thread_local` 作为类成员变量时必须是 `static` 的

#### Memory Coherence / Memory Consistency / Memory Order

##### 从缓存顺序到语言的内存模型

Coherence 约束同一位置的写入次序及可读版本。Consistency 决定不同位置的操作能以什么次序被各线程观察。以 `P1` 写入 `Y = 10` 为例，若写仍在 P1 的写缓冲器（WB，write buffer）中，P2 可能读到旧值。图中的本地 L1 与共享 L2 用来辨认两个观察点。前者可能持有最新副本，后者何时更新则随缓存协议而异。对其他核可见的边界应沿一致性协议理解。 [硬件的 Store Buffer](./Computer-Architecture.md#store-buffer-与-storeload) · [Adve 与 Gharachorloo，Memory Consistency Models](https://www.cs.cmu.edu/afs/cs/academic/class/15740-f18/www/papers/ieeemicro96-adve-consistency.pdf)

![image-20250603185505412](./C++/image-20250603185505412.png)

编译器也能在语言允许的范围内重排或合并访问。用原子操作或锁沟通跨线程约束，由编译器实现所需的硬件顺序。分析时先确定语言允许观察什么，再判断所用 CPU 怎么实现。 [ETH，Memory Models](https://spcl.inf.ethz.ch/Teaching/2019-dphpc/lectures/lecture4-memory-models.pdf)

![image-20250603233931443](./C++/image-20250603233931443.png)

顺序一致性（Sequential Consistency，SC）要求执行结果能用一条保留各处理器程序顺序的内存操作序列来解释。无缓存设计中的 write buffers with read bypassing、overlapping writes 与 nonblocking reads 要考虑这个约束。有缓存时还要协调 cache coherence protocols、detecting write completion 和 maintaining write atomicity。

**`SeqCst`（Sequentially Consistent）要求每次执行都存在一条涵盖所有 `SeqCst` 原子操作和 `SeqCst` 栅栏（fence）的共同总序。** 任意两个排入总序的操作都有先后。总序遵守这些操作之间的 strongly happens-before，包括同一线程的程序顺序，并与各原子对象的一致性规则相容。不同执行可以有不同的交错。`SeqCst` 读、写、读改写分别保有 `Acquire`、`Release`、`AcqRel` 的语义。混用其他内存序时，读值还要结合对应的规则推导。 [C++ 工作草案，原子操作顺序](https://eel.is/c++draft/atomics.order) · [Rust `Ordering::SeqCst`](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html#variant.SeqCst)

旧例的两个写记作 `W1`、`W2`，分别把初值为 0 的 `X`、`Y` 写成 1。如果 `P1` 先读 `X=1` 再读 `Y=0`，它观察到的顺序要求 `W1` 在 `W2` 之前。如果 `P2` 先读 `Y=1` 再读 `X=0`，它观察到的顺序反过来。所有操作遵守 SC 时，同一个总序无法容纳两组结果。这个例子检验两个观察者能否共同解释同一组写。

##### 原子内存序各自保证什么

下表用 Rust 的 `Ordering` 命名。C++ 的常量采用 `std::memory_order_*` 的形式，对应后缀为 `relaxed`、`acquire`、`release`、`acq_rel` 和 `seq_cst`。C++11 的六项还包括按数据依赖推导的 `std::memory_order_consume`，属于旧教材的进阶主题，具体语义按标准版本查。 [Rust Ordering](https://doc.rust-lang.org/std/sync/atomic/enum.Ordering.html) · [C++ 工作草案，原子操作顺序](https://eel.is/c++draft/atomics.order) · [C++11 顺序的旧笔记来源](https://www.zhihu.com/question/24301047/answer/83422523)

| 内存序（Rust / C++） | 编译器与硬件须满足的语义 | 典型用法 | 常见误用与排查 |
| --- | --- | --- | --- |
| `Relaxed` | 单次访问不可撕裂，同一原子对象仍有一条修改顺序（modification order）。单靠它无法同步其他变量。 | 独立监控计数 `metrics.fetch_add(1, Relaxed)`，或读取只有本线程更新且不承担交接职责的原子游标。 | 用 `ready.store(true, Relaxed)` 通知另一线程读非原子 `data`。如果对 `data` 的冲突访问没有其他同步，就会构成数据竞争，导致未定义行为（UB）。 |
| `Release`（写）+ `Acquire`（读） | A 用 `M.store(..., Release)` 发布。B 的 `M.load(Acquire)` 读自这次写入或其 release sequence 时，A 发布前的普通与原子访问 happens-before B 获取后的访问。 | SPSC Ring（单生产者、单消费者环形队列）交接槽位，自旋锁 Acquire 加锁、Release 解锁。[`Arc::drop`](./Rust.md#arc-最后一次-drop-怎样取得销毁顺序) 用 `fetch_sub(1, Release)` 递减，常规构建在归零分支经 `fence(Acquire)` 后析构。 | 标志反复写入同一个值时，要追踪读取来自哪次写。`Arc::drop` 若仅以 Relaxed 递减，其他持有者交还前的访问就缺少这条通向析构的同步边。 |
| `AcqRel` | 原子读改写（read-modify-write，RMW）读取时 Acquire，写入时 Release，既获取之前的发布，又发布自己此前的操作。只需单向保证时，RMW 也可选 Acquire 或 Release。 | `exchange`、`fetch_add` 或 CAS 成功时的读改写。 | CAS 失败只有读取，失败路径须选择读取允许的内存序。 |
| `SeqCst` | 读、写、读改写分别提供 Acquire、Release、AcqRel 的语义。所有 SeqCst 原子操作和 SeqCst fence 还共享一条总序。 | 用总序分析 [Dekker/Peterson 式双标志互检](#seqcst-怎样排除双零)。例如生产者先写 `queue_non_empty` 再读 `worker_sleeping`，worker 先写 `worker_sleeping` 再读 `queue_non_empty`。 | 热路径一律使用 SeqCst 可能带来额外的排序成本。先确认正确性证明是否依赖总序，再用目标平台的汇编和基准检验实际成本。 |

Relaxed 保留同一原子对象的可观察次序。例如一条线程先后两次 load 同一个原子，第二次读到的修改在该对象的 modification order 中不能早于第一次。这是 read-read coherence。跨地址则要另建同步。例如仅用 Relaxed 写入 `ready = true`，读方随后访问另一非原子 `data`。若冲突访问没有其他同步，C++ 数据竞争（data race）会导致未定义行为（UB）。如果 `data` 也是原子，单对象访问各自安全，跨变量的旧值组合仍要由内存序约束。 [C++ 工作草案，data races](https://eel.is/c++draft/intro.races)

##### Acquire/Release 怎样把数据交给另一线程

以单次发布为例，线程 A 先写 `data`，再对 `ready` 做 Release store。线程 B 通过 Acquire load 读到这次发布后，才读 `data`。在有其他原子读改写参与时，B 也可能读到从该 Release 开始的 release sequence 所写的值。

```mermaid
flowchart LR
    Write["A 写 data"] -->|线程内先后| Release["A 对 ready 做 Release store"]
    Release -->|B 读到这次发布| Acquire["B 对 ready 做 Acquire load"]
    Acquire -->|线程内先后| Read["B 读 data"]
```

图中间的同步边叫 synchronizes-with。把两端各自的 sequenced-before 接上，就得到 A 写 `data` happens-before B 读 `data`。C++11 旧教材使用 inter-thread happens-before 这个术语表示跨线程可推导的先后关系，旧摘记把练习定位为 `[3] Listing 5.8、5.9`。B 若读到的仍是 `ready` 的初始值，这次读取还没建立同步边。对相互独立的原子对象，也不能凭 Acquire/Release 假定所有线程共享一个全局总序。SeqCst store 和 load 读自同一次发布时仍有这条同步边，同时还需满足 SeqCst 的总序约束。 [C++11 草案，inter-thread happens-before](https://timsong-cpp.github.io/cppwp/n3337/intro.multithread) · [C++ 工作草案，原子顺序与 release sequence](https://eel.is/c++draft/atomics.order) · [Rust 原子发布例程](./Rust.md#用原子标志发布数据)

- 自旋锁的成功加锁用 Acquire，交还锁用 Release。前任持有者临界区内的写由解锁发布给下一任持有者。自旋时用于探测锁是否忙的读可用 Relaxed，取得锁时再做有 Acquire 的原子操作。
- SPSC Ring（单生产者、单消费者环形队列）用 `tail` 发布已经写好的槽位。生产者写槽后 Release 更新 `tail`，消费者 Acquire 读到对应进度后才用槽。反方向用 `head` 发布已消费的槽，生产者确认后才复用。两边单写仍需验证槽位的生命周期和容量。高频游标还可按缓存行分开布局。 [Rust 的 SPSC 端点与完整实现](./Rust.md#spsc-环形队列怎样交接槽位) · [伪共享与缓存行布局](./Computer-Architecture.md#伪共享为何让独立写入也争用)
- Rust `Arc` 的最后一个持有者需要获取其他持有者释放前的访问顺序，引用计数自身也参与同步。见 [Arc 的最后一次 drop](./Rust.md#arc-最后一次-drop-怎样取得销毁顺序)。

##### SeqCst 怎样排除双零

这个 Store Buffering（SB）例子用两个原子变量 `X`、`Y`，在线程启动前都初始化为 `0`，运行中每个变量只写一次 `1`。`W` 是写入（write / store），`R` 是读取（read / load），下标表示读写的是哪个变量。「双零」指两个 load 都返回 `0`。 [Store Buffering 与写缓冲](./Computer-Architecture.md#store-buffer-与-storeload)

| 线程 | 第一步 | 第二步 |
| --- | --- | --- |
| 线程 0 | `W_X` 写 `X = 1` | `R_Y` 读 `Y` |
| 线程 1 | `W_Y` 写 `Y = 1` | `R_X` 读 `X` |

四步都用 `SeqCst` 时，可以从初始状态按同一条总序重放四个操作。保留各线程的先写后读，每次读取取该变量此前的最近写入值。若 `W_Y` 排在 `R_Y` 前，`R_Y` 就会读到 `1`。因此，假设 `R_Y` 读到初值 `0`，它就得排在 `W_Y` 前。假设 `R_X` 也读到 `0`，它同样得排在 `W_X` 前。 [C++ 工作草案，SeqCst 的总序](https://eel.is/c++draft/atomics.order)

图中的实线是线程内的两条先后关系，虚线是两个读都返回 `0` 时要求的先后关系。把四条边接起来，就要求 `W_X` 排在自己之前。这里的 `<` 表示操作在总序中的先后。

```mermaid
flowchart LR
    WX["W_X 写 X = 1"] -->|线程 0 先写后读| RY["R_Y 读 Y"]
    RY -.->|读到 Y = 0 的条件| WY["W_Y 写 Y = 1"]
    WY -->|线程 1 先写后读| RX["R_X 读 X"]
    RX -.->|读到 X = 0 的条件| WX
```

$$
W_X < R_Y < W_Y < R_X < W_X
$$

例如 `W_X → R_Y → W_Y → R_X` 是合法的。线程 0 在 `Y` 写入前读到 `0`，线程 1 在 `X` 写入后读到 `1`。按线程 0、线程 1 的次序记，读值可以是 `(0, 1)`、`(1, 0)` 或 `(1, 1)`。

**`Release` / `Acquire` 允许双零。** 两条线程仍各自先写后读。跨线程配对时要追读取来源，`R_X` 读自 `W_X` 才会建立 `W_X → R_X` 的同步关系（synchronizes-with），`Y` 同理。两次 `Acquire` load 都可以取初始化的值并返回。此时这四步之间只有各自线程内的 happens-before，两个原子各自的修改顺序都允许这次读取。 [C++ 工作草案，Release/Acquire 的配对](https://eel.is/c++draft/atomics.order#2)

在 x86-TSO 模型中，对普通写回可缓存内存，两笔写可以先分别进入两个核自己的写缓冲（store buffer）。随后各核读取对方写的地址，此时对方的新值仍在缓冲里，两个读便都返回 `0`。两笔写可以在两个读之后才对外可见。 [x86-TSO 的双零例子](https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf)

**这个例子在 x86 上需要让本核的写先对外可见，后面的读再按这个顺序取值。** 下表是 Apple Clang 16 用 `-O2` 将 32 位原子整数的先写后读编译到 x86-64 的结果，只列访问内存的指令。 [LLVM 的 x86 原子操作映射](https://llvm.org/docs/Atomics.html#atomics-and-codegen)

| 内存序 | 写 `X = 1` | 随后读 `Y` |
| --- | --- | --- |
| `Release` / `Acquire` | `mov` | `mov` |
| `SeqCst` / `SeqCst` | `xchg` | `mov` |

带内存操作数的 `xchg` 隐式带锁，把这次写的可见性排在后续读之前。用 `mov` 写入、`MFENCE`、`mov` 读取，也能在两条线程分别建立这条约束。在 x86-TSO 模型中，`MFENCE` 要等本核屏障前的写离开写缓冲并对外可见，后面的读才在内存顺序中生效。可见性由缓存一致性系统保证，数据可以仍留在缓存里。实际指令何时发起读取由硬件决定，最终读值须遵守这个顺序。 [x86-TSO §3.1，写缓冲模型](https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf#page=4) · [§3.2，`XCHG` 与 `MFENCE` 双零测试](https://www.cl.cam.ac.uk/~pes20/weakmemory/cacm.pdf#page=6)

若 `X = 1` 先于 `Y = 1` 对外可见，线程 1 又在自己的 `Y = 1` 对外可见之后才读 `X`，因此它必读到 `1`。`Y` 先可见时，线程 0 必读到 `1`。这就是同一条总序约束在该 x86 例子里的表现。

双标志唤醒用的是同一个结构。生产者入队后将 `queue_non_empty` 置为 `true`，再读 `worker_sleeping` 决定是否发通知。Worker 先将 `worker_sleeping` 置为 `true` 表示准备睡，再读 `queue_non_empty` 确认是否还有活。如果两边都读到初始的 `false`，生产者跳过通知，worker 以为队列仍空。单次握手的这四步用 `SeqCst`，至少一方会读到对方的 `true`。

等待接口还要处理最后一次检查与实际阻塞之间的竞态。例如 worker 先读到队列空，生产者随后看见睡眠意图并发送通知，worker 最后才开始阻塞。若通知只针对当时在等的线程，这次唤醒就可能丢失。用同一把互斥锁保护队列状态的修改和检查，条件变量的 `wait` 会原子地解锁并进入等待，醒来后重新检查。完整的 Dekker/Peterson 互斥也需证明其余步骤。若标志后来会清零，还要追踪读到的 `0` 来自初值还是某次清零。 [睡眠前必须确认没错过交还](./操作系统.md#睡眠前必须确认没错过交还) · [C++ 工作草案，条件变量等待](https://eel.is/c++draft/thread.condition.condvar)

##### 同步顺序的成本

体系结构教材 §5.6 用一次写从约 50 cycles 增至 170 cycles 的例子说明实现 SC 的潜在代价，适用于教材模型。强内存序可能增加屏障或限制重排，是否产生额外指令取决于平台、操作和编译器。可以先用 C++ 默认的 SeqCst 建立容易核对的证明，Rust 需要显式传入顺序。要放宽热点上的内存序，先验证完整协议仍正确，再在目标平台量差异。 [Computer Architecture: A Quantitative Approach，5th edition，§5.6](https://acs.pub.ro/~cpop/SMPA/Computer%20Architecture%20A%20Quantitative%20Approach%20%285th%20edition%29.pdf)

#### DOD

【TODO】

[CppCon 2014: Mike Acton "Data-Oriented Design and C++"](https://www.youtube.com/watch?v=rX0ItVEVjHc)

[CppCon 2018: Stoyan Nikolov “OOP Is Dead, Long Live Data-oriented Design”](https://www.youtube.com/watch?v=yy8jQgmhbAU)

#### C++20

* Concept
* Coroutine: 可暂停和恢复的函数
  * 概念：只有并发的概念，没有并行的概念，协作式多任务；和 thread 是并列的关系
  * 分类：stack full, stackless
  * e.g. A调B，B可以随时主动suspend/resume，和A混着执行，控制权可以由用户决定
  * 场景：
    * IO Bound: 用同步样式的代码写异步逻辑
    * Ordered Tasks：性能更好
  * How to write: 有以下任一关键字的函数是coroutine
    * co_await
    * co_yield
    * co_return
  * Promise & coroutine_handle
  * co_await
  * co_yield
  * 











#### 拓展

* 《Writing Solid Code》, [douban摘要](https://book.douban.com/review/6430114/)
  * 消除所做的隐式假定
  * 一种debug方式，填充内存块的默认值
  * 指针溢出
    * [溢出问题：数组溢出，整数溢出，缓冲区溢出，栈溢出，指针溢出](https://www.cnblogs.com/fengxing999/p/11101089.html)

```c++
#define bGarbage 0xA3
bool fNewMemory(void** ppv, size_t size)
{
  char** ppb = (char**)ppv;
  ASSERT(ppv!=NULL && size!=0);
  *ppb = (char*)malloc(size);
  #ifdef DEBUG
  {
    if( *ppb != NULL )
      memset(*ppb, bGarbage, size);
  }
  #endif
  return(*ppb != NULL);
}

 void FreeMemory(void* pv)
 {
   ASSERT(pv != NULL);
   #ifdef DEBUG
   {
     memset(pv, bGarbage, sizeofBlock(pv) );
   }
   #endif
   free(pv);
 }
```

```c++
void* memchr( void *pv, unsigned char ch, size_t size )
{
    unsigned char *pch = ( unsigned char * )pv;
    unsigned char *pchEnd = pch + size;  // 可能溢出
    while( pch < pchEnd )
    {
        if( *pch == ch )
            return ( pch );
        pch ++ ;
    }
    return( NULL );
}
--->
void *memchr( void *pv, unsigned char ch, size_t size )
{
    unsigned char *pch = ( unsigned char * )pv;
    while ( size-- > 0)
    {
        if( *pch == ch )
            return( pch );
        pch ++;
    }
    return( NULL );
}
```





### 《Effective STL》

#### vector and string

##### Item 16: Know how to pass vector and string data to legacy APIs.

* Cautions
  * 不要将迭代器视作指针，don't use v.begin() instead of &v[0]
  * string: 1) 内存不保证连续；2）不保证以 null character 结尾   => c_str() 方法只适于 `const char *pString` 参数的 C API
  * vector: 不要做更改长度的操作

```c++
size_t fillArray(double *pArray, size_t arraySize);
vector<double> vd(maxNumDoubles);
vd.resize(fillArray(&vd[0], vd.size()));

size_t fillString(char 'pArray, size_t arraySize);
vector<char> vc(maxNumChars);
size_t charsWritten = fillString(&vc[0], vc.size());
string s(vc.begin(), vc.begin()+charsWritten);
```

* 引申：[Can raw pointers be used instead of iterators with STL algorithms for containers with linear storage?](https://stackoverflow.com/questions/16445957/can-raw-pointers-be-used-instead-of-iterators-with-stl-algorithms-for-containers)





### STL

十三大头文件：\<algorithm>、\<functional>、\<deque>、、\<iterator>、\<array>、\<vector>、\<list>、\<forward_list>、\<map>、\<unordered_map>、\<memory>、\<numeric>、\<queue>、\<set>、\<unordered_set>、\<stack>、\<utility>

[CppCon 2018: Jonathan Boccara “105 STL Algorithms in Less Than an Hour"](https://www.youtube.com/watch?v=2olsGf6JIkU)

[FluentC++](https://www.fluentcpp.com/posts/) 对 STL 进行了归类, It's not just `for_each`.

![world_map_of_cpp_STL_algorithms](C++/world_map_of_cpp_STL_algorithms.png)

#### queriers

```c++
// numeric algorithms
count
acculumate/(transform_)reduce // reduce的区别是输入可以没有initial value、支持parallel
                              // transform前缀在reduce之前transform
partial_sum
(transform_)inclusive_scan // 和前者的区别是支持parallel
(transform_)exclusive_scan // 和前者的区别是操作不包括自身
inner_product
adjacent_difference
sample  // 取N个random元素
  
  
// querying a property
all_of
any_of
none_of
// 对于 empty input，all_of() and none_of() return true, and any_of() return false
  
// querying a property on 2 ranges
equal
is_permutation
lexicographical_compare
mismatch -> std::pair<Iterator, Iterator>

// searching a value
// NOT SORTED
find
adjacent_find
// SORTED
equal_range
lower_bound
upper_bound // bound: insert place
binary_search

// searching a range
search   // looking for a subrange
find_end // looking for a subrange but starting from the end
find_first_of // finding any value in the subrange
  
// searching a relative value
max_element
min_element
minmax_element
```



#### permutationers

heap

```c++
std::make_heap(begin(numbers), end(numbers));  // max heap
std::make_heap(begin(numbers), end(numbers), std::greater<>{}); // min heap

numbers.push_back(num);
std::push_heap(begin(numbers), end(numbers));

std::pop_heap(begin(numbers), end(numbers));
numbers.pop_back();
// 假如不pop_back，而是持续pop_heap，相当于是在std::sort_heap

// priority_queue: https://en.cppreference.com/w/cpp/container/priority_queue
```

sort

```c++
std::sort
std::partial_sort
std::nth_element //内部是QuickSort的实现，保证了左边的都小于它，右边的都大于它
std::sort_heap
std::inplace_merge // an incremental step in MergeSort；实现利用了一块缓冲区（如果超过缓冲区长度，旋转操作后递归）
```

partitioning

* split vector https://stackoverflow.com/questions/40656792/c-best-way-to-split-vector-into-n-vector

```c++
auto it = std::partition(v.begin(), v.end(), [](int i){return i % 2 == 0;});
std::partition_point // 返回 partition 的返回值
```

其它

```c++
std::rotate
std::shuffle
std::reverse
1 2 3 4 5 --- next_permutation --> 1 2 3 5 4
          <-- prev_permutation ---
  
```



#### algos on sets

set in C++: any sorted collection (including sorted vector)

```c++
std::set_difference(a.begin(),a.end(),b.begin(),b.end(),std::back_inserter(c));
std::set_intersection
std::set_union
std::set_symmetric_difference
std::includes
std::merge
```



#### movers

```c++
std::copy(first, last, out);
std::move
std::swap_ranges
  
// e.g. 1 2 3 4 5 6 7 8 9 10 -> 1 2 3 1 2 3 4 5 9 10
std::copy_backward
std::move_backward
```



#### value modifiers

```c++
std::fill(first, last, 42);
std::uninitalized_fill

std::generate(first, last, [n = 0] () mutable { return n++; });
std::iota(first, last, 42);
std::replace(first, last, 42, 43);
```



#### structure changers

```c++
auto iter = std::remove(begin(collection), end(collection), 99);
// remove、unique
collection.erase(iter, end(collection));

```



#### algos of raw memory

```c++
fill、copy、move -> operator =
uninitilized_fill、copy、move -> ctor、copy ctor、move ctor
std::uninitilized_fill(first, last, 42);
std::destroy(first, last);
uninitilized_default_construct
uninitilized_value_construct
```



#### potpourri

Lonely islands

```c++
std::transform(begin(collection), end(collection), std::back_inserter(results), f);
// std::transform 支持二元函数 f(x,y)
std::transform(begin(collection1), end(collection1), begin(collection2), std::back_inserter(results), f);

// for_each has side-effects
std::for_each(begin(collection), end(collection), f);
```

Secret runes

```c++
stable_*   => stable_sort, stable_partition   // keep the relative order

is_* => is_sorted, is_partitioned, is_heap
is_*_until

*_copy => remove_copy, unique_copy, reverse_copy, rotate_copy, replace_copy, partition_copy, partial_sort_copy
  
*_if => find_if, find_if_not, count_if, remove_if, remove_copy_if, replace_if, replace_copy_if, copy_if
  
*_n => Raw Memory Operation + _n, generate_n, search_n, for_each_n
std::fill_n(std::back_inserter(v), 5, 42);
```



#### \<algorithm>
* sort，自己定义cmp函数，注意cmp的定义：类内静态，传参引用
  * `static bool cmp1(vector<int> &a, vector<int> &b)`

* fill_n 在-O3优化下，[效率和memset一致](https://stackoverflow.com/questions/1373369/which-is-faster-preferred-memset-or-for-loop-to-zero-out-an-array-of-doubles)，是首选

```c++
/* reset_1d_tensor Benchmark
---------------------------------------------------------------------------------------
type              for_loop  v.s.  with_slice  v.s.  fill_n
---------------------------------------------------------------------------------------
float              1.00             1.18          ** 1.00 **
Eigen::half        1.00             0.84          ** 0.65 **
int32_t            1.00             1.05          ** 1.00 **
tensorflow::int64  1.00             1.14          ** 1.00 **
std::string        1.00          ** 0.52 **          0.90
*/

inline void reset_1d_tensor(std::shared_ptr<tensorflow::Tensor>& tensor,
                            const tensorflow::TensorShape& shape,
                            tensorflow::DataType type) {
  if (!tensor || tensor->shape().dim_size(0) < shape.dim_size(0)) {
    tensor.reset(new tensorflow::Tensor(type, shape));
    return;
  }
  size_t len = shape.dim_size(0);
  if (type == tensorflow::DT_FLOAT) {
    auto data = tensor->flat<float>();
    std::fill_n(data.data(), len, 0);
  } else if (type == tensorflow::DT_HALF) {
    auto data = tensor->flat<Eigen::half>();
    std::fill_n(data.data(), len, Eigen::half(0));
  } else if (type == tensorflow::DT_INT32) {
    auto data = tensor->flat<int32_t>();
    std::fill_n(data.data(), len, 0);
  } else if (type == tensorflow::DT_INT64) {
    auto data = tensor->flat<tensorflow::int64>();
    std::fill_n(data.data(), len, 0);
  } else if (type == tensorflow::DT_STRING) {
    tensor->Slice(0, len).flat<std::string>().setConstant("");
  } else {
    LOG(FATAL) << "Unsupported tensorflow::DataType: " << type;
  }
}

inline void reset_1d_tensor_with_slice(
    std::shared_ptr<tensorflow::Tensor>& tensor,
    const tensorflow::TensorShape& shape, tensorflow::DataType type) {
  if (!tensor || tensor->shape().dim_size(0) < shape.dim_size(0)) {
    tensor.reset(new tensorflow::Tensor(type, shape));
    return;
  }
  size_t len = shape.dim_size(0);
  if (type == tensorflow::DT_FLOAT) {
    tensor->Slice(0, len).flat<float>().setZero();
  } else if (type == tensorflow::DT_HALF) {
    tensor->Slice(0, len).flat<Eigen::half>().setZero();
  } else if (type == tensorflow::DT_INT32) {
    tensor->Slice(0, len).flat<int32_t>().setZero();
  } else if (type == tensorflow::DT_INT64) {
    tensor->Slice(0, len).flat<tensorflow::int64>().setZero();
  } else if (type == tensorflow::DT_STRING) {
    tensor->Slice(0, len).flat<std::string>().setConstant("");
  } else {
    LOG(FATAL) << "Unsupported tensorflow::DataType: " << type;
  }
}
```

#### \<array>

* 适合长度在编译时就确定

```c++
void foo(const std::array<std::string, 5> &arr);

template <std::size_t N>
void bar(const std::array<std::string, N> &arr);

int main() {
  std::array<std::string, 5> arr1;
  foo(arr1); // OK
  std::array<std::string, 6> arr2;
  foo(arr2); // ERROR
  
  bar(arr1); // OK
  bar(arr2); // OK
  return 0;
}

// c++17 支持不需要指定参数个数的初始化方式（在构造函数自动推导模版类型）
static const std::array vec = {"Hello", "Kitty"};
std::string_view foo() {
  return vec[0]; // 优化成 Hello
}
```




#### \<assert.h>

* [Assert.h considered harmful](https://ftp.gnu.org/old-gnu/Manuals/nana-1.14/html_node/nana_toc.html#TOC3)

```c
# ifndef NDEBUG
# define _assert(ex)	{if (!(ex)) \
                         {(void)fprintf(stderr, \
                           "Assertion failed: file \"%s\", line %d\n", \
                           __FILE__, __LINE__);exit(1);}}
# define assert(ex)	_assert(ex)
# else
# define _assert(ex)
# define assert(ex)
# endif
```





#### \<bitset>

* 用 int 初始化 bitset

```c++
using BloomFilterStore = uint16_t
struct BloomFilterStoreItf {
    static constexpr uint32_t BIT_CAP = 16;
    static BloomFilterStore INLINE_OR_NOT insert(const BloomFilterStore store, const FID fid) {
      return neo::MurmurHash64A(reinterpret_cast<const char *>(&fid),
                                sizeof(FID), 2) | store;
    }
    static bool INLINE_OR_NOT contains(BloomFilterStore store, const FID fid) {
      auto fid_hashes = neo::MurmurHash64A(reinterpret_cast<const char *>(&fid),
                                sizeof(FID), 2);
      std::bitset<BIT_CAP> bit_hashes(fid_hashes);
      std::bitset<BIT_CAP> bit_store(store);
      for (size_t i = 0; i < BIT_CAP; i++) {
        if (bit_hashes[i] && !bit_store[i]) {
          return false;
        }
      }
      return true;
    }
}
```

#### \<chrono>

* time的单位是s，chrono可以统计ms
  * https://stackoverflow.com/questions/27846166/timenull-in-c-only-counts-seconds-not-milliseconds

```c++
auto server_time = std::chrono::duration_cast<std::chrono::microseconds>(
                           std::chrono::system_clock::now().time_since_epoch())
                           .count();
```

5s: C++14’s [duration literal suffixes](http://en.cppreference.com/w/cpp/chrono/duration#Literals)

```c++
#include <chrono>
#include <thread>
using namespace std::literals::chrono_literals;
void some_complex_work();
int main()
{
  // Fixed time step
  using clock = std::chrono::steady_clock;
  clock::time_point next_time_point = clock::now() + 5s;
  some_complex_work();
  std::this_thread::sleep_until(next_time_point);
  
  // Measure
  clock::time_point start = clock::now();
  // A long task...
  clock::time_point end = clock::now();
  clock::duration execution_time = end - start;
  
  // Sleep
  std::chrono::milliseconds sleepDuration(20);
  std::this_thread::sleep_for(sleepDuration);
  std::this_thread::sleep_for(5s);
}
```


#### \<deque> / \<queue\>
* deque，两端都能进出，双向队列，[用法详解](https://blog.csdn.net/u011630575/article/details/79923132)
* [STL之deque实现详解]( https://blog.csdn.net/u010710458/article/details/79540505?depth_1-utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromBaidu-6&utm_source=distribute.pc_relevant.none-task-blog-BlogCommendFromBaidu-6)
* deque的pop_front相当于queue的pop()
* [Do I have to lock std::queue when getting size?](https://stackoverflow.com/a/45879082)

#### \<istream>

```c++
std::ifstream ifs(filepath.str());
if (!ifs.fail()) {
	int i;
  while (ifs >> i) {
    if (ifs.peek() == ',') {
      ifs.ignore();
    }
  }
  ifs.close();
}

// read binary file to string
int read_binary_file_to_string(const std::string &filename, std::string *out) {
  std::ifstream in(filename, std::ifstream::binary);
  if (!in.is_open()) {
    return -1;
  }
  out->assign(std::istreambuf_iterator<char>(in),
              std::istreambuf_iterator<char>());
  in.close();
  return 0;
}
```




#### \<list>
* 参考[LRU cache](https://leetcode-cn.com/problems/lru-cache/)，类似双向链表的实现
  * map<int,list<pair<int,int>>::iterator> m;
* r.push_front(…), r.begin(), r.back()

#### \<math>

```c++
std::isnan(NAN);
```

#### \<string>

* `auto str = "abc"s;` 后缀s初始化string

* string_view
  * 本身不 own 内存，只是维护指针
  * 适合字符串literal，或者常驻内存的字符串

```c++
static const std::string_view str = "Hello";
auto c = str[2];
```

* [多行字符串](https://www.delftstack.com/zh/howto/cpp/cpp-multiline-string-cpp/)

```c++
int main(){
    string s1 = "This string will be printed as the"
                " one. You can include as many lines"
                "as you wish. They will be concatenated";
    copy(s1.begin(), s1.end(),
         std::ostream_iterator<char>(cout, ""));
    cout << endl;
    return EXIT_SUCCESS;
}
```

* 如何判断string是否以某一字符串开头？

`str.rfind("pattern", 0) == 0`

* [和字符数组的相互转换](https://www.cnblogs.com/fnlingnzb-learner/p/6369234.html)
  * 字符数组->str：构造函数
  * str->字符数组

```c++
char buf[10];
string str("ABCDEFG");
length = str.copy(buf, 9);
buf[length] = '\0';

char buf[10];
string str("ABCDEFG");
strcpy(buf, str.c_str());//strncpy(buf, str.c_str(), 10);
```

* [用find查找字串](https://www.cnblogs.com/wkfvawl/p/9429128.html)
  * 截取子串
    * s.substr(pos, n) 截取s中从pos开始（包括0）的n个字符的子串，并返回
    * s.substr(pos) 截取s中从从pos开始（包括0）到末尾的所有字符的子串，并返回
  * 替换子串
    * s.replace(pos, n, s1)    用s1替换s中从pos开始（包括0）的n个字符的子串
  * 查找子串
    * s.find(s1) 查找s中第一次出现s1的位置，并返回（包括0）
    * s.rfind(s1) 查找s中最后次出现s1的位置，并返回（包括0）
    * s.find_first_of(s1) 查找在s1中任意一个字符在s中第一次出现的位置，并返回（包括0）
    * s.find_last_of(s1) 查找在s1中任意一个字符在s中最后一次出现的位置，并返回（包括0）
    * s.fin_first_not_of(s1) 查找s中第一个不属于s1中的字符的位置，并返回（包括0）
    * s.fin_last_not_of(s1) 查找s中最后一个不属于s1中的字符的位置，并返回（包括0）

```c++
# Interprets an unsigned integer value in the string str.
std::string str;
std::cout << "Enter an unsigned number: ";
std::getline(std::cin,str);
size_t idx = 0;
unsigned long ul = std::stoul(str,&idx,0);
```



#### \<map>

* std::piecewise_construct
  * e.g. tensorflow/core/lib/monitoring/gauge.h

```c++
const LabelArray& label_array = {{labels...}};
cells_.emplace(std::piecewise_construct,
							 std::forward_as_tuple(label_array),
               std::forward_as_tuple(ValueType()))
```

* 用set自己的lower_bound方法，不要用`std::lower_bound`(复杂度O(n))

#### \<unordered_map>

* operator`[]` hasn't a `const` qualifier, you cannot use it directly on a const instance, use `at` instead

```c++
T& operator[](const key_type& x);
T& operator[](key_type&& x);
T&       at(const key_type& x);
const T& at(const key_type& x) const;
```

* [boost::unordered_map<>和std::unordered_map<>支持并发读吗？ - IceBear的回答 - 知乎](https://www.zhihu.com/question/21858686/answer/1722164361)
  * [cppreference: thread safety of containers](https://en.cppreference.com/w/cpp/container#.E7.BA.BF.E7.A8.8B.E5.AE.89.E5.85.A8)
    * Container operations that invalidate any iterators modify the container and cannot be executed concurrently with any operations on existing iterators even if those iterators are not invalidated.







#### \<vector>

* 初始化，可以用列表
  
  * 也可以 `int a[10]={…};vector<int> b(a,a+10); `       左闭右开
* [动态扩容](https://www.cnblogs.com/zxiner/p/7197327.html)，容量翻倍，可以用reserve()预留容量
* 方法：
  * reverse(nums.begin(),nums.end());
  * reserve(size_type n) 预先分配内存
* [关于vector的内存释放问题](https://www.cnblogs.com/jiayouwyhit/p/3878047.html)
  * 方法一：`shrink_to_fit(size_t size)`
  * 方法二：`vector<int>().swap(nums);`
  * 方法三：利用代码块和临时变量
  `
  {
    vector<int> tmp = curLevel;   
    curLevel.swap(tmp); 
  }
  `
* clear虽然不会deallocate释放空间，但是会destroy执行析构函数，所以可以用同一个空间构造节点，如果swap了就要重新分配空间再构造节点。因此对于同一个vector的重复利用，可以直接用clear();
  * 如果要每次都释放空间，也可以用`res.emplace_back(std::move(curLevel))`，涉及[emplace_back](https://www.cnblogs.com/ChrisCoder/p/9919646.html), [std::move](https://blog.csdn.net/p942005405/article/details/84644069/), [左值、右值引用](https://blog.csdn.net/p942005405/article/details/84644101), [这是一篇有关类定义的总结](https://blog.csdn.net/zzhongcy/article/details/86747794)
* [无法构造有atomic类型成员的对象的vector](https://stackoverflow.com/questions/13193484/how-to-declare-a-vector-of-atomic-in-c)



### 其它的库

#### gcc 内嵌

__builtin_clz 返回左起第一个1之前0的个数

#### boost::uuid

```c++
boost::uuids::uuid uuid = boost::uuids::random_generator()();
auto id = boost::uuids::to_string(uuid);
```

#### boost::json

```c++
try {
  boost::property_tree::ptree data_pt;
  std::istringstream json(json_result);
  boost::property_tree::read_json(json, data_pt);
  auto data1 = data_pt.get_child(KEY1);
  auto data2 = data1.get_child(KEY2);

  for (auto iter = data2.begin(); iter != data2.end(); iter++) {
    id1s.push_back(std::stoll(iter->first));
    std::string id3 = iter->second.get<std::string>(KEY3);
    id3s.push_back(std::stoll(id3));
  } 
} catch (boost::property_tree::json_parser_error e) {
  return Status::Error(
    "Parse result error. exception: %s. content: %s",
    e.message().c_str(), json_result.c_str());
} catch (boost::property_tree::ptree_bad_path e) {
  return Status::Error(
    "Get attributes error. exception: %s. content: %s",
    e.what(), json_result.c_str());
} catch (std::invalid_argument e) {
  return Status::Error("Value format is wrong: %s. content: %s",
                       e.what(), json_result.c_str());
}
```

#### \<exception>
https://blog.csdn.net/qq_37968132/article/details/82431775

`throw invalid_argument("Invalid input.");`

#### \<google::gflags>

[How To Use gflags (formerly Google Commandline Flags)](https://gflags.github.io/gflags/)

```c++
gflags::SetVersionString(get_version());
```

#### \<google::sparse_hash>

[hashmap benchmarks](https://martin.ankerl.com/2019/04/01/hashmap-benchmarks-01-overview/)

#### \<pthread.h>
* 注意使用封装好的线程操作接口

#### \<random>

* 应用
  * 注意 `thread_local` 关键字，避免多个thread在相同的时间节点产生一样的随机数


```c++
// Choose a random element
static thread_local std::mt19937 rng(std::random_device{}());
std::uniform_int_distribution<int> distribution(0, RAND_MAX-1);
int32_t sleep_time = static_cast<int32_t>(
        _expire_delta * ((double) distribution(rng)/ (RAND_MAX)) * _expire_num);
    std::this_thread::sleep_for(std::chrono::seconds(sleep_time));

// Flip a biased coin
std::random_device random_device;
std::mt19937 random_engine{random_device()};
std::bernoulli_distribution coin_distribution{0.25};
bool outcome = coin_distribution(random_engine);

// Seed a random number engine with greater unpredictability.
std::random_device r;
std::seed_seq seed_seq{r(), r(), r(), r(), r(), r()};
std::mt19937 engine{seed_seq};
```

* glibc的 [random](https://github.com/lattera/glibc/blob/master/stdlib/random.c) 函数涉及一个锁性能问题，使用的[锁](https://github.com/lattera/glibc/blob/895ef79e04a953cac1493863bcae29ad85657ee1/sysdeps/nptl/lowlevellock.h#L88)相比[pthread_mutex](https://github.com/lattera/glibc/blob/master/nptl/pthread_mutex_lock.c#L63)，没有spin的实现，性能有差距

#### \<stdarg.h>

```c++
void va_start(va_list ap, last_arg);

/* Print error message and exit with error status. */
static void
errf (char *fmt, ...)
{
  va_list ap;
  va_start (ap, fmt);
  error_print (0, fmt, ap);
  va_end (ap);
}
```




#### \<sys.h>

sche.h

`pthread_setaffinity_np(pthread_self(), sizeof(cpu_set_t), &m->set)`
* [CPU亲和性](https://blog.csdn.net/ma950924/article/details/81773719)

```c++
#ifndef __common_h__
#define __common_h__

#include <sys/time.h>
#include <sys/stat.h>
#include <assert.h>

double GetTime() {
    struct timeval t;
    int rc = gettimeofday(&t, NULL);
    assert(rc == 0);
    return (double) t.tv_sec + (double) t.tv_usec/1e6;
}

void Spin(int howlong) {
    double t = GetTime();
    while ((GetTime() - t) < (double) howlong)
    ; // do nothing in loop
}

struct timeval start, end;
gettimeofday(&start, NULL);
gettimeofday(&end, NULL);
printf("Time (seconds): %f\n\n", (float) (end.tv_usec - start.tv_usec + (end.tv_sec - start.tv_sec) * 1000000) / 1000000);


#endif // __common_h__
```





