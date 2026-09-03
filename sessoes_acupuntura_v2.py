
from supabase import create_client
import os
from dotenv import load_dotenv
import pandas as pd
import datetime as dt
import streamlit as st
import plotly.express as px
from PIL import Image


load_dotenv()

url = os.getenv('SUPABASE_URL')
key = os.getenv('SUPABASE_KEY')

supabase = create_client(url,key)


db_sessoes = supabase.table('sessoes').select('*').execute()

df_sessoes = pd.DataFrame(db_sessoes.data)
pd.set_option('display.float_format','{:.2f}'.format)
pd.set_option('display.max_columns',None)

#PAGE CONFIG
st.set_page_config(layout='wide')


st.markdown("""<style>
                .stApp{
                    background-color: #000000
                }
                </style>
                """, unsafe_allow_html=True)
logo = Image.open('logo.png')
st.image(logo, width=80)


#TRANSFORMACOES DATA

dias = {
    0: "Segunda-feira",
    1: "Terça-feira",
    2: "Quarta-feira",
    3: "Quinta-feira",
    4: "Sexta-feira",
    5: "Sábado",
    6: "Domingo"}

df_sessoes['Data'] = pd.to_datetime(df_sessoes['Data'])
df_sessoes['Dia da semana'] = df_sessoes['Data'].dt.weekday.map(dias)
df_sessoes['Ano'] = df_sessoes['Data'].dt.year
df_sessoes['Mês'] = df_sessoes['Data'].dt.month_name()
df_sessoes['Faixa etaria'] = (pd.cut(df_sessoes['Idade'],
                                     bins=[0,18,30,45,60,100],
                                     labels=['0-18','19-30','31-45', '46-60', '60+']))




st.markdown('<p style = "color: #FFFFFF; font-size: 14px; font-family: Arial;">Filtro ano</p>',unsafe_allow_html=True)
col1, col2, col3 = st.columns([2,2,2])
with col1:
    filtro_ano = st.multiselect('', sorted(df_sessoes['Ano'].unique()),
                                default=sorted(df_sessoes['Ano'].unique()))
df_filtrado = df_sessoes[df_sessoes['Ano'].isin(filtro_ano)].copy()

#VISÃO ANUAL
soma_ano = df_filtrado['Valor (R$)'].sum()

df_filtrado['Valor perc'] = (df_filtrado['Valor (R$)']/soma_ano   )*100

df_perc_anual = df_filtrado.groupby('Ano')['Valor perc'].sum().reset_index()

df_sessoes_anual = (df_filtrado.groupby('Ano').agg(
    qt_sessoes = ('Nome do Paciente','count'),
    qt_dias = ('Data','nunique'),
    numero_pacientes = ('Nome do Paciente','nunique'),
    valor_total = ('Valor (R$)','sum')
)).reset_index()

graf_anual = px.bar(df_perc_anual,x='Ano',y='Valor perc', title='Percentual por ano', text='Valor perc')
graf_anual.update_layout(
    paper_bgcolor='#000000',
    plot_bgcolor='#000000',
    font=dict(color='#FFFFFF'),
    title_font=dict(color='#FFFFFF')
)
graf_anual.update_traces(texttemplate='%{y:.2f}%',textposition='outside', marker_color='#00FFFF')

#VISÃo MENSAL
ordem_meses = ['January', 'February', 'March', 'April', 'May', 'June',
               'July', 'August', 'September', 'October', 'November', 'December']

df_sessoes_mensal = (df_filtrado.groupby(['Ano','Mês']).agg(
    qt_sessoes = ('Nome do Paciente','count'),
    numero_pacientes = ('Nome do Paciente','nunique'),
    valor_total = ('Valor (R$)','sum'))).reset_index()

ano_atual = df_sessoes['Ano'] == 2026

df_sessoes_mes = (df_sessoes[ano_atual].groupby('Mês')['Nome do Paciente'].count()).reset_index()
df_sessoes_mes['Mês'] = pd.Categorical(df_sessoes_mes['Mês'], categories=ordem_meses, ordered=True)
df_sessoes_mes = df_sessoes_mes.sort_values('Mês')


graf_mes_atual = px.bar(df_sessoes_mes,x='Mês',y='Nome do Paciente', title='Ano Vigente por mês (Filtro não se aplica)', text='Nome do Paciente')
graf_mes_atual.update_traces(textposition = 'outside',marker_color='#00FFFF')
graf_mes_atual.update_layout(xaxis_title='Mês', yaxis_title='Qtd Pacientes', paper_bgcolor='#000000',
    plot_bgcolor='#000000',
    font=dict(color='#FFFFFF'),
    title_font=dict(color='#FFFFFF'))


#tipo consulta consolidado
df_tipo_consulta = (df_filtrado.groupby('Tipo de Consulta').agg(
    qt_tipo_consulta = ('Tipo de Consulta','count'),
    valor_tipo_consulta = ('Valor (R$)','sum'),
    turno_relevante = ('Turno',lambda x: x.mode()[0])
)).reset_index()


df_tipo_consulta_anual = (df_filtrado.groupby(['Ano','Tipo de Consulta']).agg(
    qt_tipo_consulta = ('Tipo de Consulta','count'),
    valor_tipo_consulta = ('Valor (R$)','sum'),
    turno_relevante = ('Turno',lambda x: x.mode()[0])
)).reset_index()


df_terapeuta_cons = (df_filtrado.groupby('Terapeuta').agg(
    qt_sessoes = ('Nome do Paciente','count'),
    media_idade = ('Idade','mean'),
    valor_total = ('Valor (R$)','sum')

)).reset_index()

#PACIENTE
df_paciente =(df_filtrado.pivot_table(
    index='Nome do Paciente',
    columns='Terapeuta',
    values='Valor (R$)',
    aggfunc='count'
)).fillna(0).astype(int).reset_index()


#FAIXA ETARIA


df_faixa_anual = df_filtrado.groupby(['Ano','Faixa etaria'])['Nome do Paciente'].count().reset_index()
graf_etaria=px.bar(df_faixa_anual,x='Ano', y='Nome do Paciente', color='Faixa etaria',
                   barmode='group', title= 'Quantidade de consulta por faixa etária',text='Nome do Paciente')
graf_etaria.update_traces(textposition='outside')
graf_etaria.update_layout(xaxis_title='Ano', yaxis_title='Qtd Pacientes',paper_bgcolor='#000000',
    plot_bgcolor='#000000',
    font=dict(color='#FFFFFF'),
    title_font=dict(color='#FFFFFF'),
    legend=dict(font=dict(color='#FFFFFF')))

#MOTIVO

df_motivo= (df_filtrado.groupby(['Motivo','Faixa etaria']).agg(
    qt_sessoes = ('Nome do Paciente','count')
    )).reset_index()

df_motivo_ano= df_filtrado.groupby(['Ano','Motivo'])['Nome do Paciente'].count().reset_index()

graf_motivo= px.bar(df_motivo_ano,x='Ano', y='Nome do Paciente', color='Motivo',
                    barmode='group',title='Motivos de Consulta', text='Nome do Paciente')
graf_motivo.update_traces(textposition='outside')
graf_motivo.update_layout(xaxis_title='Ano', yaxis_title='Qtd Pacientes',paper_bgcolor='#000000',
    plot_bgcolor='#000000',
    font=dict(color='#FFFFFF'),
    title_font=dict(color='#FFFFFF'),
    legend=dict(font=dict(color='#FFFFFF')))







st.markdown('<h2 style="color: #FFFFFF;" >Anual</h2>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Faturamento anual</h4>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">A clínica cresceu de 2024 para 2026?</h4>', unsafe_allow_html=True)

st.dataframe(df_sessoes_anual)  
st.plotly_chart(graf_anual)

st.markdown('<h2 style="color: #FFFFFF;" >Mensal</h2>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Qual mês tem mais consultas?</h4>', unsafe_allow_html=True)
st.dataframe(df_sessoes_mensal)
st.plotly_chart(graf_mes_atual)

st.markdown('<h2 style="color: #FFFFFF;" >Tipo de Consulta</h2>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Qual tipo de consulta gera mais receita?</h4>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Qual turno é mais lucrativo?</h4>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Manhã ou tarde tem mais demanda?</h4>', unsafe_allow_html=True)
st.dataframe(df_tipo_consulta)

st.markdown('<h2 style="color: #FFFFFF;" >Tipo de Consulta Anual</h2>', unsafe_allow_html=True)
st.dataframe(df_tipo_consulta_anual)

st.markdown('<h2 style="color: #FFFFFF;" >Terapeutas</h2>', unsafe_allow_html=True)
st.dataframe(df_terapeuta_cons)

st.markdown('<h2 style="color: #FFFFFF;" >Pacientes</h2>', unsafe_allow_html=True)
st.dataframe(df_paciente)
st.plotly_chart(graf_etaria)

st.markdown('<h2 style="color: #FFFFFF;" >Motivos</h2>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Doenças físicas ou psicológicas predominam?</h4>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Qual o motivo mais comum por faixa etária?</h4>', unsafe_allow_html=True)
st.markdown('<h4 style="color: #FFFFFF;">Houve aumento de casos de ansiedade/depressão ao longo dos anos?</h4>', unsafe_allow_html=True)
st.dataframe(df_motivo)
st.plotly_chart(graf_motivo)




