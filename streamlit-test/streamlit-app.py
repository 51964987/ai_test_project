import streamlit as st

st.title("我的第一个Streamlit应用")
name = st.text_input("请输入名字")
score = st.slider("分数", 0, 100)
st.write(f"你好 {name}，分数：{score}")
