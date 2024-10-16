# sqlite dockerfile 说明
在sqlite的dockerfile组织目录中，第一层为版本号，第二层为对应的实验版本
下面对实验版本的描述
## 实验描述
- original
  最原始的版本，只修改了git的版本号
- with_LLM_Generate_1
  第一个实验版本，添加了LLM生成的分割代码
- just_LLM_Generate
  第二个实验版本，删除原input，只采用LLM生成的测试用例
- with_zrcl_mutator_0
  此版本是第一次添加了zrcl_mutator的版本的docker，内容进行了大概，不再clone Squirrel，而是直接clone zrcl_mutator
- just_zrcl_mutator_0
  此版本为只有ZRCL_mutator的版本
- with_LLM_Generate_showmap
  使用showmap启动fuzz