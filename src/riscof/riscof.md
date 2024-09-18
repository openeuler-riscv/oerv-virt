# 1.概述
RISCOF是一个基于python的框架，其目的是可以测试一套RISC-V架构设计是否兼容和符合标准的RISC-V参考模型。

RISCOF主要有两个主要的外部工具组成：
1. RISCV-CONFIG：用于验证用户提供的输入ISA YAML的合法性，RISCV-CONFIG将捕获YAML文件中与RISC-V规范的冲突，之后将生成RISCOF接受的YAML标准版本。
2. RISCV-ISAC：此工具用于分析YAML是否全面覆盖了RISC-V规范中的各个部分和质量评估。

# 2.执行流程

1. 准备阶段
    - 输入：
        * 提供一个YAML文件，用于描述其RISC-V实现的具体配置
        * 提供一个python插件，要求按照既定要求和规范编写，能够实现在用户的实现上编译和模拟测试

2. 测试选择和配置
    - 选择适用测试：
        * 标准化后的YAML文件会被送往 Test Selector utility，从测试池中筛选出适用于用户实现的测试。
        * 被选中的测试会被记录在一个新的YAML文件中，形成 test-list

3. 编译执行
    - 测试的编译和执行
        * test-list 被传递给用户和参考模型定义的python插件，启动各平台上的测试编译和执行。
        * 每个测试都按照测试规范执行，并会在对应的内存区域生成一个签名。

4. 结果验证与测试报告
    - 签名比对
        * Python 插件负责从各自系统中提取测试的内存签名文件
        * RISCOF 根据签名文件的匹配情况，来判断测试是否通过
    - 生成报告
        * 执行结束，RISCOF生成一个HTML报告


# 3.部署流程

1. python >= 3.6.0
2. 安装RISCOF
```
pip3 install riscof
```
3. 安装RISCV-GUN工具链，如果运行在RISCV-GUN机器上则不需要

```
sudo apt-get install autoconf 
sudo apt-get install automake 
sudo apt-get install autotools-dev 
sudo apt-get install curl 
sudo apt-get install python3 
sudo apt-get install libmpc-dev 
sudo apt-get install libmpfr-dev 
sudo apt-get install libgmp-dev 
sudo apt-get install gawk 
sudo apt-get install build-essential 
sudo apt-get install bison 
sudo apt-get install flex 
sudo apt-get install texinfo 
sudo apt-get install gperf 
sudo apt-get install libtool 
sudo apt-get install patchutils 
sudo apt-get install bc 
sudo apt-get install zlib1g-dev 
sudo apt-get install libexpat-dev
sudo apt-get install libnewlib-dev
sudo apt-get install device-tree-compiler

```
下载riscv-gnu-toolchain及全部引用子模块
```
git clone --recursive https://github.com/riscv/riscv-gnu-toolchain
```
编译riscv32-unknown-elf-gcc
```
cd riscv-gnu-toolchain
mkdir build
cd build
../configure --prefix=/opt/RISCV/riscv64 --with-arch=rv32imc --with-abi=ilp32d
sudo make -jN

```
编译 riscv64-unknown-elf-gcc
```
cd riscv-gnu-toolchain
mkdir build
cd build
../configure --prefix=/opt/RISCV/riscv64 --with-arch=rv64imc --with-abi=lp64d
sudo make -jN 

```
4. 安装插件模型
安装两个重要的RISC-V参考模型，Spike和SAIL，一般作用于RISCOF中的参考模型
```
sudo apt-get install opam  build-essential libgmp-dev z3 pkg-config zlib1g-dev
opam init -y --disable-sandboxing
opam switch create ocaml-base-compiler.4.06.1
opam install sail -y
eval $(opam config env)
git clone https://github.com/riscv/sail-riscv.git
cd sail-riscv
make
ARCH=RV32 make
ARCH=RV64 make
```
并把`c_emulator/riscv_sim_RV64` 和 `c_emulator/riscv_sim_RV32` 加入环境变量。
```
sudo apt-get install device-tree-compiler
git clone https://github.com/riscv-software-src/riscv-isa-sim.git
cd riscv-isa-sim
mkdir build
cd build
../configure --prefix=/path/to/install
make -jN
make install
```
并把`/path/to/install`加入到环境变量

5. 创建环境文件
    - config.ini：这是一个基本的配置文件
        * 插件名称：指定待测设备(DUT)和参考模型(reference)
        * 插件路径：指向DUT插件和reference的文件路径
        * YAML路径：指向riscv-config的YAML文件路径，描述了DUT和ISA平台特性。
    - dut-plugin目录：包含用于测试的DUT模型的python插件
    - reference-plugin目录：RISCOF的参考模型

RISCOF 通过以下命令为用户生成 DUT 和参考模型的标准预建模板
```
riscof setup --dutname=spike
```
6. 测试官方测试
拉取来自riscv-arch-test的测试文件
> https://github.com/riscv-non-isa/riscv-arch-test
```
riscof --verbose info arch-tests --clone
```
7. 运行RISCOF

分为三部

   - 检查输入的YAML文件是否符合标准
   ```
   riscof validateyaml --config=config.ini
   ```
   - 生成需要在模型上运行的测试列表
   ```
   riscof testlist --config=config.ini --suite=riscv-arch-test/riscv-test-suite/ --env=riscv-arch-test/riscv-test-suite/env

   ```

   - 在每一个模型上运行测试并比较签名并判断是否正确
   ```
   riscof run --config=config.ini --suite=riscv-arch-test/riscv-test-suite/ --env=riscv-arch-test/riscv-test-suite/env

   ```
# 4.汇编宏和测试标签

预定义宏和特定于模型的宏，保证了每个测试的可移植性。

## 4.1 必需的预定义宏

这些宏在compilance_test.h中定义。

- `RVTEST_ISA(isa_str[,isa_str]*)`
    * 用于定义测试虚拟机的指令集架构(ISA)，可以指定一个或多个ISA。如果指定了多个ISA，系统会从中选择一个与被测试ISA兼容的一个或者多个组合。
    * 在测试的开始处声明，以指明测试需要的指令集
- `RVTEST_CODE_BEGIN`
    * 包含一个初始化例程，预先加载所有通用寄存器，并具有唯一值
    * 寄存器t0和t1被初始化指向标签`rvtest_code_begin`和`rvtest_code_end`
    * 此宏标记测试代码部分的开始，所有测试代码都不能出现在此宏之前
- `RVTEST_CODE_END`
    * 强制执行16字节边界对齐
    * 如启用了trap handling，该宏包含整个测试所需要的trap handling处理代码
    * 此宏标记测试代码的结束，测试代码不能出现在此宏之后
- `RVTEST_DATA_BEGIN`
    * 数据区从16字节边界开始对其
    * 如启用了trap handling，将包含用于保存trap handling中使用的临时寄存器区域和其他的必要使用区域。
    * 此宏标记测试数据部分的开始
- `RVTEST_DATA_END`
    * 使用`rvtest_data_end`定位数据部分的结束
    * 此宏标记测试数据部分的结束
- `RVTEST_CASE(CaseName, CondStr)`
    * `ConStr`判断测试用例是否启用，并可设置变量名称
    * 测试用例必须使用`#ifdef CaseName/#endif`来封闭边界
    * 此宏定义只有满足特定条件时执行的测试用例
## 4.2 必需的模型定义的宏

这些宏定义在model_test.h中

- `RVMODEL_DATA_BEGIN`
    * 必须从16字节边界开始对齐
    * 此宏定义签名区域的开始，使用此宏创建一个标签，标记签名区域的开始。
- `RVMODEL_DATA_END`
    * 必须从16字节边界开始对齐
    * 此宏标记签名区域的结束。
- `RVMODEL_HALT`
    * 此宏定义测试目标的停止，用于测试完成或者不支持的行为时终止。
## 4.3 可选的预定义宏

- `RVTEST_SIGBASE(BaseReg, Val)`
    * 用于更新签名值的基础寄存器
    * BaseReg加载值Val
    * hidden_offset初始化为0
- `RVTEST_SIGUPD(BaseReg, SigReg [, Offset])`
    * 如果参数存在Offset，则hidden_offset设置为Offset
    * SigReg存储在BaseReg[hidden_offset]的位置
    * hidden_offset会进行自增，以便连续使用时顺序存储签名值
- `RVTEST_BASEUPD(BaseReg[oldBase[, newOff]])`
    * 更新BaseReg寄存器的值，使其指向签名区域之后的一个新的位置
    * BaseReg 被更新的基础寄存器
    * oldBase可选，原始基础寄存器，如未指定，将使用BaseReg本身
    * newOff可选，添加到原始寄存器的偏移量，如未指定，则为0
    * 计算新的基地址的方式为：oldReg + newOff + hidden_offset
    * 执行宏之后，hidden_offset被重置为0
- `RVTEST_SIGUPD_F(BaseReg, SigReg, FlagReg [, Offset])`
    * 将 SigReg 和 FlagReg 的内容顺序存储到由基础寄存器（BaseReg）和内部偏移量（hidden_offset）指定的内存地址
    * BaseReg 指定签名数据存储的基本内存地址的基础寄存器
    * SigReg 主数据寄存器，其内容将被写入内存
    * FlagReg 标志寄存器，其内容也将被写入内存，存储在SigReg之后
    * Offset 可选，提供一个初始偏移量，如果存在，则hidden_offset将被设置为Offset + (XLEN * 2)
    * XLEN 表示数据宽度，32或者64
    * hidden_offset在数据写入后会自增，确保下一次使用此宏时，新的数据可以顺序存储在接下来的内存位置。自增的值通常是两倍的 XLEN
## 4.4 可选的模型定义的宏

- `RVMODEL_BOOT`
    * 用于定义和初始化测试目标的启动代码。封装了启动期间需要执行的所有必要操作，确保测试环境正确设置
    * 在实际测试程序开始执行之前，RVMODEL_BOOT 宏作为测试代码的一部分被执行
    * 设置mtvec寄存器
    * 数据准备，如果需要，从持久存储设备复制数据到主存
- `RVMODEL_IO_INIT` 
    * 初始化用于调试的I/O系统
    * 如果使用任何其他RV_MODEL_IO_* 宏，必须首先调用此宏
- `RVMODEL_IO_ASSERT_GPR_EQ(ScrReg, Reg, Value)`
    * 断言通用寄存器(GPR)的值是否等于预期值
    * 如果Reg的值不等于Value，则输出一条调试信息
    * 使用一个临时寄存器ScrReg来存储输出信息，但这个寄存器的值，不能保持持久
- `RVMODEL_IO_WRITE_STR(ScrReg, String)`
    * 输出调试字符串
    * 输出String指定的消息
    * 使用ScrReg作为临时寄存器来处理输出，同样的这个寄存器的值，不能保持持久
- `RVMODEL_SET_MSW_INT`
    * 设置机器软件中断
    * 如果目标并没有声明此宏，则测试环境将强制其为空宏
- `RVMODEL_CLEAR_MSW_INT`
    * 清除机器软件中断
    * 如果目标并没有声明此宏，则测试环境将强制其为空宏
- `RVMODEL_CLEAR_MTIMER_INT`
    * 清除机器时间中断
    * 如果目标并没有声明此宏，则测试环境将强制其为空宏
- `RVMODEL_CLEAR_MEXT_INT`
    * 清除机器外部中断
    * 如果目标并没有声明此宏，则测试环境将强制其为空宏
- `RVMODEL_MTVEC_ALIGN`
    * 指定一个整数，用于 .align 汇编指令，与陷阱处理程序（trap handler）的起始地址对齐
    * 基于实现特定的MTVEC的对齐限制
    * 如果目标未声明此宏，默认为 .align 6，表示陷阱处理程序的起始地址需要64字节对齐。
## 4.5 必须的标签

测试必须定义一个`rvtest_entry_point`标签，来告诉链接器从何处开始执行测试程序。在编译和链接过程中，这个标签被用来设置程序的起始执行地址。

它通常位于 RVMODEL_BOOT 宏之前并且应属于该text.init部分。

