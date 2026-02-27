#!/usr/bin/env python
# -*- coding: utf-8 -*-

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from collections import Counter
import re
import io
import sys
import ast
import pdfplumber  # 解析PDF
import docx        # 解析Word
import io
import re
from collections import Counter
# ============= 安全设置编码（只在需要时） =============
try:
    # 检查是否在Streamlit Cloud环境
    if not st.runtime.exists():
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
except:
    pass  # 如果出错就忽略

# ============= 页面配置 =============
st.set_page_config(
    page_title="霍兰德职业兴趣推荐系统",
    page_icon="🎯",
    layout="wide"
)
# ============= 自定义CSS样式 =============
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #424242;
        text-align: center;
        margin-bottom: 2rem;
    }
    .type-card {
        background-color: #f0f2f6;
        border-radius: 10px;
        padding: 20px;
        margin: 10px;
        text-align: center;
    }
    .type-title {
        font-size: 1.8rem;
        font-weight: bold;
        margin-bottom: 10px;
    }
    .type-desc {
        font-size: 1rem;
        color: #666;
    }
    .job-card {
        background-color: white;
        border: 1px solid #ddd;
        border-radius: 8px;
        padding: 15px;
        margin: 10px 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .match-badge {
        background-color: #1E88E5;
        color: white;
        padding: 5px 10px;
        border-radius: 15px;
        font-size: 0.9rem;
        display: inline-block;
    }
    .stButton>button {
        width: 100%;
        background-color: #1E88E5;
        color: white;
        font-size: 1.2rem;
        padding: 0.5rem;
    }
    .deploy-info {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
        margin: 10px 0;
        font-size: 0.9rem;
        color: #666;
    }
</style>
""", unsafe_allow_html=True)

# ============= 加载数据 =============
@st.cache_data
def load_data():
    """加载处理好的职业数据"""
    try:
        # 请确保这个文件路径正确
        df = pd.read_excel("jobs_analyzed_统一单位.xlsx")
        
        # 处理霍兰德得分列（如果是字符串格式）
        if '霍兰德得分' in df.columns and isinstance(df['霍兰德得分'].iloc[0], str):
            df['霍兰德得分'] = df['霍兰德得分'].apply(ast.literal_eval)
        
        # 处理行业列表列（如果是字符串格式）
        if '行业列表' in df.columns and isinstance(df['行业列表'].iloc[0], str):
            try:
                df['行业列表'] = df['行业列表'].apply(ast.literal_eval)
            except:
                # 如果转换失败，保持原样
                pass
        
        # ============= 职业去重 =============
        st.sidebar.markdown('<div class="deploy-info">', unsafe_allow_html=True)
        st.sidebar.write(f"📊 去重前岗位数量: {len(df)}")
        
        # 规范化职业名称，用于去重
        def normalize_job_name(job_name):
            """规范化职业名称，去除薪资、福利等信息"""
            job_name = str(job_name)
            
            # 保存原始名称
            original = job_name
            
            # 1. 去除薪资信息（数字+K/千/万）
            job_name = re.sub(r'\d+\.?\d*[kK]', '', job_name)  # 5K, 8K
            job_name = re.sub(r'\d+\.?\d*千', '', job_name)    # 5千, 8千
            job_name = re.sub(r'\d+\.?\d*万', '', job_name)    # 5万, 8万
            job_name = re.sub(r'\d+-\d+', '', job_name)        # 5-8, 10-15
            job_name = re.sub(r'\d+\.?\d*', '', job_name)      # 任何单独的数字
            
            # 2. 去除福利信息
            welfare_words = ['双休', '周末双休', '单休', '大小周', '五险一金', '社保', '公积金', 
                          '包吃', '包住', '餐补', '房补', '交通补助', '话补', '加班补助',
                          '弹性工作', '年终奖', '绩效奖金', '全勤奖', '股票期权', '提成',
                          '奖金', '补贴', '补助', '福利', '待遇优厚', '薪资面议']
            for word in welfare_words:
                job_name = job_name.replace(word, '')
            
            # 3. 去除括号及其内容
            job_name = re.sub(r'\([^)]*\)', '', job_name)
            job_name = re.sub(r'（[^）]*）', '', job_name)
            job_name = re.sub(r'\[[^\]]*\]', '', job_name)
            job_name = re.sub(r'【[^】]*】', '', job_name)
            
            # 4. 去除特殊字符和多余空格
            job_name = re.sub(r'[^\w\u4e00-\u9fff]', ' ', job_name)  # 只保留中文、英文、数字
            job_name = re.sub(r'\s+', ' ', job_name)
            job_name = job_name.strip()
            
            # 如果规范化后为空或太短，返回原始名称的前几个字符
            if not job_name or len(job_name) < 2:
                # 尝试提取中文部分
                chinese_part = re.findall(r'[\u4e00-\u9fff]+', original)
                if chinese_part:
                    job_name = ' '.join(chinese_part)
                else:
                    job_name = original[:8]
            
            return job_name
        
        # 添加规范化后的职业名称
        df['职业_规范'] = df['职业'].apply(normalize_job_name)
        
        # 显示规范化后的唯一职业数
        st.sidebar.write(f"📋 规范化后的唯一职业数: {df['职业_规范'].nunique()}")
        
        # 按规范化名称分组，保留薪资最高的那条记录
        df_sorted = df.sort_values('平均薪资_千', ascending=False)
        
        # 定义分组后的聚合规则
        aggregation_rules = {
            '职业': 'first',  # 保留原始职业名称（薪资最高的那个）
            '薪资': 'first',
            '行业列表': 'first',
            '主要类型': 'first',
            '平均薪资_千': 'first',
            '霍兰德得分': 'first'
        }
        
        # 如果有其他列，也保留第一个值
        for col in df.columns:
            if col not in aggregation_rules and col not in ['职业_规范', 'index']:
                aggregation_rules[col] = 'first'
        
        # 执行去重
        df_deduplicated = df_sorted.groupby('职业_规范').agg(aggregation_rules).reset_index()
        
        # 删除辅助列
        df_deduplicated = df_deduplicated.drop(columns=['职业_规范'])
        
        # 显示去重结果
        st.sidebar.write(f"✅ 去重后岗位数量: {len(df_deduplicated)}")
        st.sidebar.write(f"✨ 去除了 {len(df) - len(df_deduplicated)} 个重复岗位")
        st.sidebar.markdown('</div>', unsafe_allow_html=True)
        
        return df_deduplicated
        
    except Exception as e:
        st.sidebar.error(f"加载数据失败: {e}")
        # 创建示例数据用于测试
        return create_sample_data()

def create_sample_data():
    """创建示例数据（用于测试）"""
    data = {
        '职业': ['数据分析师', '销售经理', 'UI设计师', '人力资源专员', '机械工程师'],
        '薪资': ['15.0-25.0千/月', '20.0-35.0千/月', '12.0-20.0千/月', '8.0-15.0千/月', '10.0-18.0千/月'],
        '行业列表': [['互联网/电子商务'], ['市场营销'], ['互联网/电子商务'], ['人力资源'], ['机械/设备/重工']],
        '主要类型': ['I', 'E', 'A', 'S', 'R'],
        '平均薪资_千': [20.0, 27.5, 16.0, 11.5, 14.0],
        '霍兰德得分': [
            {'R': 0.1, 'I': 0.6, 'A': 0.1, 'S': 0.1, 'E': 0.1, 'C': 0.0},
            {'R': 0.0, 'I': 0.2, 'A': 0.1, 'S': 0.2, 'E': 0.5, 'C': 0.0},
            {'R': 0.1, 'I': 0.1, 'A': 0.6, 'S': 0.1, 'E': 0.1, 'C': 0.0},
            {'R': 0.0, 'I': 0.1, 'A': 0.1, 'S': 0.6, 'E': 0.1, 'C': 0.1},
            {'R': 0.5, 'I': 0.3, 'A': 0.0, 'S': 0.0, 'E': 0.1, 'C': 0.1},
        ]
    }
    return pd.DataFrame(data)

# ============= 获取所有行业列表 =============
def get_all_industries(df):
    """从数据框中提取所有唯一的行业"""
    all_industries = set()
    
    for ind_list in df['行业列表']:
        if isinstance(ind_list, list):
            for ind in ind_list:
                if isinstance(ind, str) and ind.strip():
                    all_industries.add(ind.strip())
        elif isinstance(ind_list, str):
            # 如果是字符串，尝试分割
            if ',' in ind_list:
                for ind in ind_list.split(','):
                    clean_ind = ind.strip().strip('[]\'\"')
                    if clean_ind:
                        all_industries.add(clean_ind)
            else:
                clean_ind = ind_list.strip().strip('[]\'\"')
                if clean_ind:
                    all_industries.add(clean_ind)
    
    return sorted(all_industries)

# ============= 霍兰德类型说明 =============
HOLLAND_TYPES = {
    'R': {
        'name': '现实型',
        'color': '#FF6B6B',
        'icon': '🛠️',
        'description': '喜欢动手操作、机械维修、户外工作，擅长使用工具和设备。',
        'traits': ['实际', '稳重', '踏实', '动手能力强'],
        'examples': ['机械工程师', '电工', '建筑师', '驾驶员']
    },
    'I': {
        'name': '研究型',
        'color': '#4ECDC4',
        'icon': '🔬',
        'description': '喜欢思考分析、科学研究、解决问题，擅长理论和抽象思维。',
        'traits': ['好奇', '理性', '独立', '分析能力强'],
        'examples': ['数据分析师', '研究员', '程序员', '科学家']
    },
    'A': {
        'name': '艺术型',
        'color': '#FFD93D',
        'icon': '🎨',
        'description': '喜欢创意表达、艺术创作、自由发挥，富有想象力和创造力。',
        'traits': ['创意', '感性', '表达力强', '追求个性'],
        'examples': ['设计师', '作家', '音乐人', '摄影师']
    },
    'S': {
        'name': '社会型',
        'color': '#6BCB77',
        'icon': '🤝',
        'description': '喜欢帮助他人、沟通协作、教育培训，擅长人际交往。',
        'traits': ['友善', '乐于助人', '善于沟通', '有同理心'],
        'examples': ['教师', '护士', '心理咨询师', '人力资源']
    },
    'E': {
        'name': '企业型',
        'color': '#FF9F1C',
        'icon': '💼',
        'description': '喜欢领导管理、说服他人、达成目标，擅长决策和冒险。',
        'traits': ['自信', '有野心', '善于说服', '领导力强'],
        'examples': ['销售经理', '创业者', '项目经理', '市场总监']
    },
    'C': {
        'name': '常规型',
        'color': '#A9A9A9',
        'icon': '📊',
        'description': '喜欢数据处理、规范流程、组织整理，擅长执行和细节。',
        'traits': ['细心', '有条理', '执行力强', '稳重'],
        'examples': ['会计', '行政助理', '档案管理员', '数据录入员']
    }
}

# ============= 用户性格测评问题 =============
# ============= 用户性格测评问题 =============
QUESTIONS = [
    {
        'question': '你在团队中通常扮演什么角色？',
        'options': [
            ('执行者，负责具体操作', {'R': 2, 'C': 1}),
            ('思考者，负责分析问题', {'I': 2, 'C': 1}),
            ('创意者，提供新点子', {'A': 2, 'I': 1}),
            ('协调者，维护团队和谐', {'S': 2, 'E': 1}),
            ('领导者，带领团队前进', {'E': 2, 'S': 1}),
            ('组织者，确保流程规范', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你最喜欢的休闲活动是什么？',
        'options': [
            ('动手制作或修理东西', {'R': 2, 'A': 1}),
            ('阅读、研究感兴趣的话题', {'I': 2, 'C': 1}),
            ('绘画、音乐、写作等创作', {'A': 2, 'I': 1}),
            ('和朋友聚会、社交活动', {'S': 2, 'E': 1}),
            ('参加竞赛、追求成就', {'E': 2, 'S': 1}),
            ('整理物品、规划日程', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你在工作中最看重什么？',
        'options': [
            ('稳定的环境和清晰的指令', {'C': 2, 'R': 1}),
            ('能够深入研究和解决问题', {'I': 2, 'R': 1}),
            ('自由发挥创意的空间', {'A': 2, 'I': 1}),
            ('帮助他人、服务社会', {'S': 2, 'A': 1}),
            ('晋升机会和领导地位', {'E': 2, 'S': 1}),
            ('工作成果能被量化评估', {'C': 2, 'E': 1})
        ]
    },
    {
        'question': '朋友通常怎么形容你？',
        'options': [
            ('踏实可靠、动手能力强', {'R': 2, 'C': 1}),
            ('聪明理性、爱思考', {'I': 2, 'R': 1}),
            ('有创意、与众不同', {'A': 2, 'I': 1}),
            ('善解人意、好相处', {'S': 2, 'A': 1}),
            ('有魄力、能带动气氛', {'E': 2, 'S': 1}),
            ('细心周到、有条理', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '面对新任务，你的第一反应是？',
        'options': [
            ('先动手尝试，在实践中学习', {'R': 2, 'C': 1}),
            ('先收集资料，分析清楚再做', {'I': 2, 'C': 1}),
            ('思考如何用创意的方式完成', {'A': 2, 'I': 1}),
            ('考虑如何与他人合作完成', {'S': 2, 'E': 1}),
            ('思考如何快速高效地达成目标', {'E': 2, 'S': 1}),
            ('制定详细的计划和步骤', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你更喜欢哪种学习方式？',
        'options': [
            ('动手实践，边做边学', {'R': 2, 'A': 1}),
            ('阅读书籍、查阅资料', {'I': 2, 'C': 1}),
            ('通过创意项目学习', {'A': 2, 'I': 1}),
            ('小组讨论、交流学习', {'S': 2, 'E': 1}),
            ('参加培训、听讲座', {'E': 2, 'C': 1}),
            ('按步骤、按计划学习', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '在消费时，你更看重什么？',
        'options': [
            ('产品的实用性和耐用性', {'R': 2, 'C': 1}),
            ('产品的科技含量和创新', {'I': 2, 'R': 1}),
            ('产品的设计和美感', {'A': 2, 'I': 1}),
            ('能否和朋友一起分享', {'S': 2, 'A': 1}),
            ('品牌价值和身份象征', {'E': 2, 'S': 1}),
            ('性价比和实用性', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你如何处理压力？',
        'options': [
            ('通过运动或手工活动释放', {'R': 2, 'A': 1}),
            ('分析问题根源，寻找解决方案', {'I': 2, 'C': 1}),
            ('通过艺术创作表达情绪', {'A': 2, 'I': 1}),
            ('找朋友倾诉、寻求支持', {'S': 2, 'E': 1}),
            ('制定计划，积极应对', {'E': 2, 'C': 1}),
            ('按部就班，一步步解决', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你更喜欢哪种工作环境？',
        'options': [
            ('户外、车间、现场', {'R': 2, 'C': 1}),
            ('实验室、图书馆、安静的环境', {'I': 2, 'C': 1}),
            ('工作室、创意空间', {'A': 2, 'I': 1}),
            ('开放的办公室、团队氛围', {'S': 2, 'E': 1}),
            ('会议室、谈判桌、商务场合', {'E': 2, 'S': 1}),
            ('办公室、有规律的工位', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你最喜欢的电影类型是？',
        'options': [
            ('动作片、冒险片', {'R': 2, 'E': 1}),
            ('科幻片、悬疑片', {'I': 2, 'C': 1}),
            ('文艺片、音乐片', {'A': 2, 'I': 1}),
            ('剧情片、情感片', {'S': 2, 'A': 1}),
            ('商战片、传记片', {'E': 2, 'S': 1}),
            ('纪录片、历史片', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你如何做决定？',
        'options': [
            ('凭直觉和实际操作', {'R': 2, 'A': 1}),
            ('收集信息，理性分析', {'I': 2, 'C': 1}),
            ('凭创意和灵感', {'A': 2, 'I': 1}),
            ('考虑他人感受和意见', {'S': 2, 'E': 1}),
            ('快速果断，追求结果', {'E': 2, 'S': 1}),
            ('按规则和流程', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你更喜欢哪种解决问题的方式？',
        'options': [
            ('动手操作，现场解决', {'R': 2, 'C': 1}),
            ('分析研究，找到规律', {'I': 2, 'C': 1}),
            ('换个角度，创新解决', {'A': 2, 'I': 1}),
            ('寻求帮助，团队协作', {'S': 2, 'E': 1}),
            ('谈判协商，达成共识', {'E': 2, 'S': 1}),
            ('按标准流程处理', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你对未来的职业期待是什么？',
        'options': [
            ('成为技术专家、工匠', {'R': 2, 'I': 1}),
            ('成为研究员、科学家', {'I': 2, 'C': 1}),
            ('成为艺术家、设计师', {'A': 2, 'I': 1}),
            ('成为教师、咨询师', {'S': 2, 'A': 1}),
            ('成为管理者、企业家', {'E': 2, 'S': 1}),
            ('成为专业人士、骨干', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你最喜欢的学科是？',
        'options': [
            ('体育、物理实验、手工', {'R': 2, 'A': 1}),
            ('数学、物理、化学', {'I': 2, 'C': 1}),
            ('美术、音乐、文学', {'A': 2, 'I': 1}),
            ('语文、历史、政治', {'S': 2, 'A': 1}),
            ('商业、经济、管理', {'E': 2, 'S': 1}),
            ('会计、统计、计算机', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你如何安排周末？',
        'options': [
            ('做手工、户外运动、修理东西', {'R': 2, 'A': 1}),
            ('看书、研究感兴趣的话题', {'I': 2, 'C': 1}),
            ('画画、写作、听音乐', {'A': 2, 'I': 1}),
            ('和朋友聚会、参加社交活动', {'S': 2, 'E': 1}),
            ('参加培训、拓展人脉', {'E': 2, 'S': 1}),
            ('整理房间、规划下周', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你更喜欢哪种沟通方式？',
        'options': [
            ('直接了当，说重点', {'R': 2, 'E': 1}),
            ('逻辑清晰，有理有据', {'I': 2, 'C': 1}),
            ('生动形象，有创意', {'A': 2, 'I': 1}),
            ('温和体贴，顾及感受', {'S': 2, 'A': 1}),
            ('有说服力，能带动人', {'E': 2, 'S': 1}),
            ('条理分明，按顺序', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你对科技产品的态度？',
        'options': [
            ('喜欢拆解、研究原理', {'R': 2, 'I': 1}),
            ('关注最新科技发展', {'I': 2, 'C': 1}),
            ('喜欢创意科技产品', {'A': 2, 'I': 1}),
            ('喜欢能连接社交的产品', {'S': 2, 'E': 1}),
            ('关注商业价值', {'E': 2, 'S': 1}),
            ('够用就好，注重实用', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你最喜欢的旅游方式是？',
        'options': [
            ('自驾游、户外探险', {'R': 2, 'A': 1}),
            ('文化考察、博物馆之旅', {'I': 2, 'C': 1}),
            ('艺术之旅、摄影采风', {'A': 2, 'I': 1}),
            ('结伴而行、团队旅游', {'S': 2, 'E': 1}),
            ('商务旅行、考察', {'E': 2, 'S': 1}),
            ('跟团游、有计划的旅行', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你如何处理日常杂事？',
        'options': [
            ('马上动手处理', {'R': 2, 'C': 1}),
            ('想清楚再做', {'I': 2, 'C': 1}),
            ('换个方式处理', {'A': 2, 'I': 1}),
            ('找人帮忙一起做', {'S': 2, 'E': 1}),
            ('快速搞定，不管细节', {'E': 2, 'S': 1}),
            ('按顺序、有条理地做', {'C': 2, 'R': 1})
        ]
    },
    {
        'question': '你更喜欢哪种类型的书籍？',
        'options': [
            ('实用手册、工具书', {'R': 2, 'C': 1}),
            ('科普读物、专业书籍', {'I': 2, 'C': 1}),
            ('小说、诗歌、艺术类', {'A': 2, 'I': 1}),
            ('心理学、人际关系', {'S': 2, 'A': 1}),
            ('成功学、商业传记', {'E': 2, 'S': 1}),
            ('管理类、励志类', {'C': 2, 'R': 1})
        ]
    }
]

# ============= 计算用户霍兰德得分 =============
def calculate_user_scores(answers):
    """根据用户答案计算霍兰德得分"""
    scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    
    for answer in answers:
        for h_type, value in answer.items():
            scores[h_type] += value
    
    # 归一化到0-1范围
    max_score = max(scores.values()) if max(scores.values()) > 0 else 1
    for h_type in scores:
        scores[h_type] = scores[h_type] / max_score
    
    return scores

# ============= 推荐职业（优化版） =============
def recommend_jobs(user_scores, df, top_n=10, min_salary=0, industries=None):
    """根据用户得分推荐职业（保证多样性）"""
    recommendations = []
    
    # 为每个岗位计算匹配度
    for _, row in df.iterrows():
        job_scores = row['霍兰德得分']
        
        # 计算余弦相似度
        dot_product = sum(user_scores[t] * job_scores[t] for t in user_scores)
        user_norm = sum(v**2 for v in user_scores.values()) ** 0.5
        job_norm = sum(v**2 for v in job_scores.values()) ** 0.5
        
        if user_norm > 0 and job_norm > 0:
            similarity = dot_product / (user_norm * job_norm)
        else:
            similarity = 0
        
        # 薪资过滤
        if row['平均薪资_千'] < min_salary:
            continue
        
        # 行业过滤
        if industries:
            job_industries = row['行业列表']
            if isinstance(job_industries, list):
                if not any(ind in job_industries for ind in industries):
                    continue
            elif isinstance(job_industries, str):
                if not any(ind in job_industries for ind in industries):
                    continue
        
        # 提取核心职业名称（用于去重）
        core_name = extract_core_name(row['职业'])
        
        recommendations.append({
            '职业': row['职业'],
            '核心名称': core_name,
            '薪资': row['薪资'],
            '行业': ', '.join(row['行业列表']) if isinstance(row['行业列表'], list) else str(row['行业列表']),
            '匹配度': similarity,
            '匹配度百分比': round(similarity * 100, 1),
            '主要类型': row['主要类型'],
            '平均薪资_千': row['平均薪资_千']
        })
    
    # 按匹配度排序
    recommendations.sort(key=lambda x: x['匹配度'], reverse=True)
    
    # ============= 多样性筛选 =============
    diverse_recommendations = []
    seen_core_names = set()  # 记录已经出现过的核心职业
    seen_industries = set()  # 记录已经出现过的行业
    
    # 先取匹配度最高的几个，但要保证多样性
    for job in recommendations:
        core_name = job['核心名称']
        industry = job['行业']
        
        # 判断条件：
        # 1. 如果这个核心职业还没出现过，直接加入
        # 2. 如果核心职业出现过，但行业完全不同，也可以考虑
        # 3. 如果核心职业和行业都相似，跳过
        
        if core_name not in seen_core_names:
            # 新的核心职业，直接加入
            diverse_recommendations.append(job)
            seen_core_names.add(core_name)
            seen_industries.add(industry)
        elif industry not in seen_industries:
            # 核心职业相似但行业不同，以较低优先级加入
            # 检查是否已经有太多相似的
            similar_count = sum(1 for r in diverse_recommendations if r['核心名称'] == core_name)
            if similar_count < 2:  # 最多允许2个相似核心职业
                diverse_recommendations.append(job)
                seen_industries.add(industry)
        # 其他情况跳过（避免重复）
    
    # 如果多样性筛选后不够数量，补充一些匹配度高的
    if len(diverse_recommendations) < top_n:
        for job in recommendations:
            if job not in diverse_recommendations:
                # 检查是否已经有太多相似的
                core_name = job['核心名称']
                similar_count = sum(1 for r in diverse_recommendations if r['核心名称'] == core_name)
                if similar_count < 2:  # 最多允许2个相似
                    diverse_recommendations.append(job)
                if len(diverse_recommendations) >= top_n:
                    break
    
    # 如果还不够，就按匹配度补充
    if len(diverse_recommendations) < top_n:
        for job in recommendations:
            if job not in diverse_recommendations:
                diverse_recommendations.append(job)
                if len(diverse_recommendations) >= top_n:
                    break
    
    # 重新按匹配度排序
    diverse_recommendations.sort(key=lambda x: x['匹配度'], reverse=True)
    
    # 转换为显示格式
    result = []
    for job in diverse_recommendations[:top_n]:
        result.append({
            '职业': job['职业'],
            '薪资': job['薪资'],
            '行业': job['行业'],
            '匹配度': job['匹配度百分比'],
            '主要类型': job['主要类型'],
            '平均薪资_千': job['平均薪资_千']
        })
    
    return result

# ============= 提取核心职业名称 =============
def extract_core_name(job_name):
    """从完整职业名称中提取核心部分（用于去重）"""
    job_name = str(job_name)
    
    # 常见的职业关键词
    job_keywords = [
        '数据分析', '数据挖掘', '数据开发', '数据仓库', '数据工程',
        '算法', '机器学习', '深度学习', '人工智能', 'AI',
        '产品经理', '产品运营', '产品助理',
        '运营', '用户运营', '内容运营', '活动运营',
        '市场', '营销', '推广', '投放', '广告',
        '销售', '商务', '渠道', '客户经理',
        '前端', '后端', '全栈', '移动开发', '测试',
        'UI', 'UX', '交互设计', '视觉设计', '平面设计',
        '人力资源', 'HR', '招聘', '培训', '行政',
        '财务', '会计', '出纳', '审计',
        '客服', '售后', '技术支持',
        '采购', '供应链', '物流',
        '法务', '律师', '合规',
        '咨询', '顾问', '分析师'
    ]
    
    # 尝试匹配关键词
    for keyword in job_keywords:
        if keyword in job_name:
            return keyword
    
    # 如果没有匹配到关键词，返回前4个字符
    return job_name[:4]
# ============= 主应用 =============
def main():
    # 加载数据
    df = load_data()
    
    # 获取所有行业
    all_industries = get_all_industries(df)
    
    # 侧边栏
    with st.sidebar:
        st.image("https://img.icons8.com/color/96/000.com/bar-chart.png", width=80)
        st.title("🎯 霍兰德职业测评")
        st.markdown("---")
        
        # 测评模式选择
        mode = st.radio(
            "选择测评方式",
            ["📝 快速测评", "✋ 手动选择类型", "📄 上传简历分析", "🔍 直接搜索"]
            
        )
        
        st.markdown("---")
        
        # 筛选条件
        st.subheader("筛选条件")
        
        # 薪资筛选
        min_salary = st.slider(
            "最低月薪 (千/月)",
            min_value=0,
            max_value=50,
            value=0,
            step=1,
            help="单位：千/月 (5千=5, 1万=10, 2万=20)"
        )
        
        # 行业筛选
        if all_industries:
            selected_industries = st.multiselect(
                "选择行业",
                all_industries
            )
        else:
            selected_industries = st.multiselect(
                "选择行业",
                ["暂无数据"]
            )
            st.info("⚠️ 行业数据正在加载中...")
    
    # 主内容区
    st.markdown('<h1 class="main-header">🎯 霍兰德职业兴趣推荐系统</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">发现最适合你的职业方向</p>', unsafe_allow_html=True)
    
    # ============= 根据模式显示不同内容 =============
    # 注意：以下所有代码都在 main() 函数内部，需要缩进
    
    if mode == "📝 快速测评":
        st.markdown("## 📋 请回答以下问题，我们将为你分析最适合的职业类型")
        
        # 初始化session state
        if 'answers' not in st.session_state:
            st.session_state.answers = []
        if 'step' not in st.session_state:
            st.session_state.step = 0
        
        # 显示问题
        if st.session_state.step < len(QUESTIONS):
            q = QUESTIONS[st.session_state.step]
            
            # 显示进度条
            progress = (st.session_state.step) / len(QUESTIONS)
            st.progress(progress, text=f"问题 {st.session_state.step + 1}/{len(QUESTIONS)}")
            
            st.markdown(f"### 📝 第 {st.session_state.step + 1} 题")
            st.markdown(f"**{q['question']}**")
            
            # 创建选项按钮（两列布局）
            cols = st.columns(2)
            for i, (option_text, scores) in enumerate(q['options']):
                with cols[i % 2]:
                    if st.button(option_text, key=f"q_{st.session_state.step}_{i}", use_container_width=True):
                        st.session_state.answers.append(scores)
                        st.session_state.step += 1
                        st.rerun()
            
            # 添加"上一题"按钮（不是第一题时才显示）
            if st.session_state.step > 0:
                col1, col2, col3 = st.columns([1, 1, 1])
                with col2:
                    if st.button("◀ 上一题", use_container_width=True):
                        st.session_state.answers.pop()  # 删除最后一个答案
                        st.session_state.step -= 1
                        st.rerun()
        
        # 完成测评
        if st.session_state.step >= len(QUESTIONS) and st.session_state.answers:
            st.success("✅ 测评完成！正在为你分析...")
            
            # 计算用户得分
            user_scores = calculate_user_scores(st.session_state.answers)
            
            # 显示用户性格雷达图
            st.markdown("## 🎯 你的性格类型分析")
            
            col1, col2 = st.columns([1, 1])
            
            with col1:
                # 雷达图
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=[user_scores[t] for t in ['R', 'I', 'A', 'S', 'E', 'C']],
                    theta=['现实型 R', '研究型 I', '艺术型 A', '社会型 S', '企业型 E', '常规型 C'],
                    fill='toself',
                    name='你的得分',
                    line_color='#1E88E5'
                ))
                fig.update_layout(
                    polar=dict(
                        radialaxis=dict(
                            visible=True,
                            range=[0, 1]
                        )),
                    showlegend=False,
                    height=400
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                # 显示主要类型
                sorted_types = sorted(user_scores.items(), key=lambda x: x[1], reverse=True)
                main_type = sorted_types[0][0]
                second_type = sorted_types[1][0]
                
                st.markdown(f"### 你的主导类型：{HOLLAND_TYPES[main_type]['icon']} {HOLLAND_TYPES[main_type]['name']}")
                st.markdown(f"**{HOLLAND_TYPES[main_type]['description']}**")
                st.markdown(f"**典型特质：** {', '.join(HOLLAND_TYPES[main_type]['traits'])}")
                
                st.markdown(f"### 次要类型：{HOLLAND_TYPES[second_type]['icon']} {HOLLAND_TYPES[second_type]['name']}")
                
                # 得分详情
                st.markdown("### 详细得分")
                for h_type, score in sorted_types:
                    st.progress(score, text=f"{HOLLAND_TYPES[h_type]['icon']} {h_type}: {score:.2f}")
            
            # 推荐职业
            st.markdown("---")
            st.markdown("## 💼 为你推荐的职业")
            
            recommendations = recommend_jobs(
                user_scores, 
                df, 
                top_n=10,
                min_salary=min_salary,
                industries=selected_industries if selected_industries != ["暂无数据"] else None
            )
            
            if recommendations:
                for job in recommendations:
                    with st.container():
                        st.markdown(f"""
                        <div class="job-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin:0">{job['职业']}</h3>
                                    <p style="color: #666; margin:5px 0">行业：{job['行业']}</p>
                                    <p style="color: #666; margin:5px 0">薪资：{job['薪资']}</p>
                                </div>
                                <div style="text-align: right;">
                                    <span class="match-badge">匹配度 {job['匹配度']}%</span>
                                    <p style="color: #1E88E5; margin:5px 0">类型：{job['主要类型']}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
                
                # 可视化推荐结果
                st.markdown("### 📊 推荐岗位匹配度分布")
                rec_df = pd.DataFrame(recommendations)
                fig = px.bar(rec_df.head(10), x='职业', y='匹配度', 
                            color='匹配度', color_continuous_scale='viridis',
                            title="Top 10 推荐岗位匹配度")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.warning("没有找到匹配的岗位，请调整筛选条件")
            
            # 在底部添加两个按钮
            st.markdown("---")
            col1, col2, col3 = st.columns([1, 1, 1])
            with col1:
                if st.button("◀ 返回上一题", use_container_width=True):
                    st.session_state.step = len(QUESTIONS) - 1
                    st.session_state.answers.pop()
                    st.rerun()
            with col2:
                if st.button("🔄 重新测评", use_container_width=True):
                    st.session_state.answers = []
                    st.session_state.step = 0
                    st.rerun()

    # ============= 上传简历分析模式 =============
    elif mode == "📄 上传简历分析":
        st.markdown("## 📄 上传你的简历")
        st.markdown("支持 PDF 或 Word 格式，我们将为你分析技能特长并推荐匹配岗位")
        
        # 文件上传
        uploaded_file = st.file_uploader(
            "选择简历文件", 
            type=['pdf', 'docx'],
            help="支持 .pdf 或 .docx 格式"
        )
        
        if uploaded_file is not None:
            # 显示文件信息
            file_details = {
                "文件名": uploaded_file.name,
                "文件大小": f"{uploaded_file.size / 1024:.1f} KB",
                "文件类型": uploaded_file.type
            }
            st.json(file_details)
            
            # 解析简历
            with st.spinner("正在解析简历，请稍候..."):
                parser = ResumeParser()
                file_bytes = uploaded_file.getvalue()
                
                # 判断文件类型
                if uploaded_file.type == "application/pdf":
                    resume_data = parser.parse(file_bytes, "pdf")
                elif uploaded_file.type == "application/vnd.openxmlformats-officedocument.wordprocessingml.document":
                    resume_data = parser.parse(file_bytes, "docx")
                else:
                    st.error("不支持的文件格式")
                    resume_data = None
            
            if resume_data:
                st.success("✅ 简历解析成功！")
                
                # 显示解析结果
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📋 基本信息")
                    st.markdown(f"**姓名**：{resume_data['姓名']}")
                    st.markdown(f"**学历**：{resume_data['学历']}")
                    st.markdown(f"**工作经验**：{resume_data['工作经验']}年")
                
                with col2:
                    st.markdown("### 🛠️ 技能特长")
                    if resume_data['技能']:
                        for skill in resume_data['技能']:
                            st.markdown(f"- {skill}")
                    else:
                        st.markdown("未检测到明确技能关键词")
                
                # 从技能推断霍兰德得分
                skill_holland = calculate_holland_from_skills(resume_data['技能'])
                
                # 结合测评（可选）
                st.markdown("---")
                st.markdown("### 🎯 完善你的职业兴趣")
                st.markdown("如果想获得更精准的推荐，可以补充回答以下问题（可选）")
                
                with st.expander("点击补充兴趣测评"):
                    if 'resume_answers' not in st.session_state:
                        st.session_state.resume_answers = []
                    if 'resume_step' not in st.session_state:
                        st.session_state.resume_step = 0
                    
                    # 这里复用之前的测评问题
                    if st.session_state.resume_step < len(QUESTIONS):
                        q = QUESTIONS[st.session_state.resume_step]
                        st.markdown(f"**{q['question']}**")
                        
                        cols = st.columns(2)
                        for i, (opt, scores) in enumerate(q['options']):
                            with cols[i % 2]:
                                if st.button(opt, key=f"resume_q_{st.session_state.resume_step}_{i}", use_container_width=True):
                                    st.session_state.resume_answers.append(scores)
                                    st.session_state.resume_step += 1
                                    st.rerun()
                        
                        # 添加"上一题"按钮
                        if st.session_state.resume_step > 0:
                            if st.button("◀ 上一题", key="resume_prev"):
                                st.session_state.resume_answers.pop()
                                st.session_state.resume_step -= 1
                                st.rerun()
                    
                    if st.session_state.resume_step >= len(QUESTIONS) and st.session_state.resume_answers:
                        interest_holland = calculate_user_scores(st.session_state.resume_answers)
                        st.success("兴趣测评完成！")
                        
                        # 显示兴趣测评的雷达图小预览
                        fig_small = go.Figure()
                        fig_small.add_trace(go.Scatterpolar(
                            r=[interest_holland[t] for t in ['R', 'I', 'A', 'S', 'E', 'C']],
                            theta=['R', 'I', 'A', 'S', 'E', 'C'],
                            fill='toself',
                            name='兴趣'
                        ))
                        fig_small.update_layout(height=200, margin=dict(l=20, r=20, t=20, b=20))
                        st.plotly_chart(fig_small, use_container_width=True)
                    else:
                        interest_holland = None
                
                # 综合霍兰德得分
                if interest_holland:
                    # 融合：技能60% + 兴趣40%
                    final_holland = {}
                    for t in ['R', 'I', 'A', 'S', 'E', 'C']:
                        final_holland[t] = skill_holland.get(t, 0) * 0.6 + interest_holland.get(t, 0) * 0.4
                    
                    st.markdown("### 🔄 综合性格分析")
                    st.markdown("（技能60% + 兴趣40%）")
                else:
                    final_holland = skill_holland
                    st.markdown("### 🔄 基于技能的性格分析")
                
                # 显示雷达图
                fig = go.Figure()
                fig.add_trace(go.Scatterpolar(
                    r=[final_holland[t] for t in ['R', 'I', 'A', 'S', 'E', 'C']],
                    theta=['现实型 R', '研究型 I', '艺术型 A', '社会型 S', '企业型 E', '常规型 C'],
                    fill='toself',
                    name='你的画像'
                ))
                fig.update_layout(polar=dict(radialaxis=dict(range=[0, 1])), height=400)
                st.plotly_chart(fig, use_container_width=True)
                
                # 推荐岗位
                st.markdown("---")
                st.markdown("## 💼 为你推荐的岗位")
                
                recommendations = recommend_jobs(
                    final_holland,
                    df,
                    top_n=10,
                    min_salary=min_salary,
                    industries=selected_industries if selected_industries != ["暂无数据"] else None
                )
                
                if recommendations:
                    for job in recommendations:
                        with st.container():
                            st.markdown(f"""
                            <div class="job-card">
                                <div style="display: flex; justify-content: space-between; align-items: center;">
                                    <div>
                                        <h3 style="margin:0">{job['职业']}</h3>
                                        <p style="color: #666; margin:5px 0">行业：{job['行业']}</p>
                                        <p style="color: #666; margin:5px 0">薪资：{job['薪资']}</p>
                                    </div>
                                    <div style="text-align: right;">
                                        <span class="match-badge">匹配度 {job['匹配度']}%</span>
                                        <p style="color: #1E88E5; margin:5px 0">类型：{job['主要类型']}</p>
                                    </div>
                                </div>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    # 技能匹配分析
                    st.markdown("### 📊 技能匹配分析")
                    
                    # 简单的技能匹配建议
                    top_job = recommendations[0]['职业']
                    skill_text = "、".join(resume_data['技能'][:5]) if resume_data['技能'] else "暂无"
                    st.info(f"💡 **{top_job}** 岗位与你的技能匹配度较高。你的技能特长：{skill_text}")
                    
                    # 可视化匹配度分布
                    st.markdown("### 📊 推荐岗位匹配度分布")
                    rec_df = pd.DataFrame(recommendations)
                    fig = px.bar(rec_df.head(10), x='职业', y='匹配度', 
                                color='匹配度', color_continuous_scale='viridis',
                                title="Top 10 推荐岗位匹配度")
                    st.plotly_chart(fig, use_container_width=True)
                else:
                    st.warning("没有找到匹配的岗位，请调整筛选条件")
                
                # 重新上传按钮
                if st.button("🔄 重新上传", use_container_width=True):
                    st.session_state.resume_answers = []
                    st.session_state.resume_step = 0
                    st.rerun()

    elif mode == "✋ 手动选择类型":
        st.markdown("## 🎯 选择你的霍兰德性格类型")
        
        # 显示六种类型的说明卡片
        cols = st.columns(3)
        for i, (h_type, info) in enumerate(HOLLAND_TYPES.items()):
            with cols[i % 3]:
                st.markdown(f"""
                <div class="type-card" style="border-left: 5px solid {info['color']};">
                    <div class="type-title">{info['icon']} {info['name']}</div>
                    <div class="type-desc">{info['description']}</div>
                    <div style="margin-top:10px; font-size:0.9rem;">
                        <strong>典型特质：</strong> {', '.join(info['traits'])}
                    </div>
                    <div style="margin-top:10px; font-size:0.9rem;">
                        <strong>典型职业：</strong> {', '.join(info['examples'][:3])}
                    </div>
                </div>
                """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # 用户选择类型
        col1, col2 = st.columns(2)
        with col1:
            primary_type = st.selectbox(
                "选择你的主要性格类型",
                options=list(HOLLAND_TYPES.keys()),
                format_func=lambda x: f"{HOLLAND_TYPES[x]['icon']} {HOLLAND_TYPES[x]['name']}"
            )
        
        with col2:
            secondary_type = st.selectbox(
                "选择你的次要性格类型（可选）",
                options=['无'] + list(HOLLAND_TYPES.keys()),
                format_func=lambda x: '无' if x == '无' else f"{HOLLAND_TYPES[x]['icon']} {HOLLAND_TYPES[x]['name']}"
            )
        
        # 强度调节
        st.markdown("### 性格强度调节")
        col1, col2 = st.columns(2)
        with col1:
            primary_strength = st.slider("主要类型强度", 0.5, 1.0, 0.8, 0.1)
        with col2:
            secondary_strength = st.slider("次要类型强度", 0.0, 0.8, 0.4, 0.1) if secondary_type != '无' else 0.0
        
        if st.button("🔍 开始推荐", type="primary"):
            # 构建用户得分
            user_scores = {t: 0.0 for t in HOLLAND_TYPES}
            user_scores[primary_type] = primary_strength
            if secondary_type != '无':
                user_scores[secondary_type] = secondary_strength
            
            # 归一化
            max_score = max(user_scores.values())
            if max_score > 0:
                for t in user_scores:
                    user_scores[t] = user_scores[t] / max_score
            
            # 推荐职业
            st.markdown("---")
            st.markdown("## 💼 为你推荐的职业")
            
            recommendations = recommend_jobs(
                user_scores, 
                df, 
                top_n=10,
                min_salary=min_salary,
                industries=selected_industries if selected_industries != ["暂无数据"] else None
            )
            
            if recommendations:
                for job in recommendations:
                    with st.container():
                        st.markdown(f"""
                        <div class="job-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin:0">{job['职业']}</h3>
                                    <p style="color: #666; margin:5px 0">行业：{job['行业']}</p>
                                    <p style="color: #666; margin:5px 0">薪资：{job['薪资']}</p>
                                </div>
                                <div style="text-align: right;">
                                    <span class="match-badge">匹配度 {job['匹配度']}%</span>
                                    <p style="color: #1E88E5; margin:5px 0">类型：{job['主要类型']}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("没有找到匹配的岗位，请调整筛选条件")

    else:  # 直接搜索模式
        st.markdown("## 🔍 直接搜索职业")
        
        # 搜索框
        search_term = st.text_input("输入职业关键词", placeholder="例如：数据分析师、销售经理...")
        
        if search_term:
            # 过滤数据
            filtered_df = df[df['职业'].str.contains(search_term, case=False, na=False)]
            
            if not filtered_df.empty:
                st.success(f"找到 {len(filtered_df)} 个相关职业")
                
                for _, row in filtered_df.iterrows():
                    with st.container():
                        # 处理行业显示
                        if isinstance(row['行业列表'], list):
                            industry_display = ', '.join(row['行业列表'])
                        else:
                            industry_display = str(row['行业列表'])
                        
                        st.markdown(f"""
                        <div class="job-card">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <h3 style="margin:0">{row['职业']}</h3>
                                    <p style="color: #666; margin:5px 0">行业：{industry_display}</p>
                                    <p style="color: #666; margin:5px 0">薪资：{row['薪资']}</p>
                                </div>
                                <div style="text-align: right;">
                                    <p style="color: #1E88E5; margin:5px 0">类型：{row['主要类型']}</p>
                                </div>
                            </div>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("没有找到匹配的职业")

        # 显示所有行业统计
        st.markdown("---")
        st.markdown("### 📊 数据概览")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("总岗位数", len(df))
        with col2:
            avg_salary = df['平均薪资_千'].mean()
            st.metric("平均薪资", f"{avg_salary:.1f}千/月 ({avg_salary/10:.1f}万/月)")
        with col3:
            # 处理可能的空数据
            if all_industries:
                st.metric("主要行业", all_industries[0] if all_industries else "暂无数据")
            else:
                st.metric("主要行业", "暂无数据")


# ============= 简历解析模块 =============
class ResumeParser:
    """简历解析器：从PDF/Word中提取信息"""
    
    def __init__(self):
        # 常见技能关键词库
        self.skill_keywords = {
            'Python': ['python', 'python', '派森'],
            'Java': ['java', '爪哇'],
            'JavaScript': ['javascript', 'js', 'ecmascript'],
            'SQL': ['sql', 'mysql', 'postgresql', '数据库'],
            '数据分析': ['数据分析', '数据挖掘', '数据清洗', 'etl'],
            '机器学习': ['机器学习', '深度学习', 'tensorflow', 'pytorch', 'ai'],
            '前端开发': ['html', 'css', 'vue', 'react', 'angular'],
            '后端开发': ['django', 'flask', 'spring', 'nodejs'],
            '产品经理': ['产品经理', '需求分析', '原型设计', 'axure', '磨刀'],
            '项目管理': ['项目管理', '敏捷开发', 'scrum', 'pmp'],
            '运营': ['用户运营', '内容运营', '活动运营', '新媒体'],
            '设计': ['photoshop', 'ps', 'ui设计', '交互设计', 'figma'],
            '办公软件': ['excel', 'word', 'ppt', 'wps', 'office'],
            '沟通能力': ['沟通', '协调', '团队合作', '表达'],
        }
        
        # 学历关键词
        self.education_keywords = {
            '博士': ['博士', 'phd'],
            '硕士': ['硕士', '研究生'],
            '本科': ['本科', '学士'],
            '大专': ['大专', '专科'],
            '高中': ['高中', '中专']
        }
        
        # 工作年限正则
        self.year_pattern = r'(\d+)[\s\-]*年'
    
    def extract_text_from_pdf(self, file_bytes):
        """从PDF提取文本"""
        text = ""
        try:
            with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            return text
        except Exception as e:
            st.error(f"PDF解析失败: {e}")
            return ""
    
    def extract_text_from_docx(self, file_bytes):
        """从Word提取文本"""
        try:
            doc = docx.Document(io.BytesIO(file_bytes))
            text = "\n".join([para.text for para in doc.paragraphs])
            return text
        except Exception as e:
            st.error(f"Word解析失败: {e}")
            return ""
    
    def extract_skills(self, text):
        """提取技能关键词"""
        text_lower = text.lower()
        found_skills = []
        
        for skill, keywords in self.skill_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    found_skills.append(skill)
                    break
        
        return list(set(found_skills))  # 去重
    
    def extract_education(self, text):
        """提取最高学历"""
        text_lower = text.lower()
        
        for edu, keywords in self.education_keywords.items():
            for keyword in keywords:
                if keyword in text_lower:
                    return edu
        return "未知"
    
    def extract_experience_years(self, text):
        """提取工作年限"""
        matches = re.findall(self.year_pattern, text)
        if matches:
            # 取最大年限
            years = [int(m) for m in matches]
            return max(years)
        return 0
    
    def extract_name(self, text):
        """尝试提取姓名（简单规则）"""
        # 常见姓名开头
        lines = text.split('\n')
        for line in lines[:10]:  # 只看前10行
            line = line.strip()
            # 姓名通常在2-4个汉字，且在第一行附近
            if 2 <= len(line) <= 4 and re.match(r'^[\u4e00-\u9fa5]+$', line):
                return line
        return "未知"
    
    def parse(self, file_bytes, file_type):
        """主解析函数"""
        # 提取文本
        if file_type == "pdf":
            text = self.extract_text_from_pdf(file_bytes)
        elif file_type == "docx":
            text = self.extract_text_from_docx(file_bytes)
        else:
            return None
        
        if not text:
            return None
        
        # 提取各项信息
        result = {
            '姓名': self.extract_name(text),
            '学历': self.extract_education(text),
            '工作经验': self.extract_experience_years(text),
            '技能': self.extract_skills(text),
            '原始文本': text[:500] + "..."  # 预览
        }
        
        return result
# ============= 技能-霍兰德映射 =============
SKILL_HOLLAND_MAP = {
    # 研究型 I
    'Python': 'I',
    'Java': 'I',
    'JavaScript': 'I',
    'SQL': 'I',
    '数据分析': 'I',
    '机器学习': 'I',
    '算法': 'I',
    
    # 艺术型 A
    '设计': 'A',
    'UI设计': 'A',
    '交互设计': 'A',
    'PS': 'A',
    '创意': 'A',
    
    # 社会型 S
    '沟通能力': 'S',
    '团队合作': 'S',
    '协调': 'S',
    '客户服务': 'S',
    
    # 企业型 E
    '项目管理': 'E',
    '产品经理': 'E',
    '运营': 'E',
    '销售': 'E',
    '管理': 'E',
    
    # 常规型 C
    '办公软件': 'C',
    'Excel': 'C',
    '文档': 'C',
    
    # 现实型 R
    '机械': 'R',
    '设备': 'R',
    '维修': 'R',
}

def calculate_holland_from_skills(skills):
    """根据技能计算霍兰德得分"""
    scores = {'R': 0, 'I': 0, 'A': 0, 'S': 0, 'E': 0, 'C': 0}
    
    for skill in skills:
        if skill in SKILL_HOLLAND_MAP:
            h_type = SKILL_HOLLAND_MAP[skill]
            scores[h_type] += 1
    
    # 归一化
    total = sum(scores.values())
    if total > 0:
        for k in scores:
            scores[k] = scores[k] / total
    
    return scores

# ============= 运行应用 =============
if __name__ == "__main__":
    main()  # 只有这一处调用
