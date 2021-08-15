import matplotlib.pyplot as plt
from matplotlib import font_manager
import matplotlib.widgets as pwd
import matplotlib
import pandas as pd
import glob
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
import sqlite3
import numpy as np

file_path = 'D:/데이터교육/vaccine_data/'
font_path = 'C:/Windows/Fonts/경기천년제목_Light.ttf'
font_name = font_manager.FontProperties(fname=font_path).get_name()
matplotlib.rc('font',family = font_name)

col1 = "#0f2839"
col2 = "#4a94b0"
col3 = "#2195f2"
col4 = "#b7e5ff"
col5 = "#d7d7d7"
col6 = "#faf8f6"
col7 = "#e3b94d"
col8 = "#da3738"


conn = sqlite3.connect(':memory:')
cur = conn.cursor()

#csv파일들을 읽어오는 함수
def get_files(file_path):
    #경로 내의 모든 csv파일명을 리스트로 생성
    csv = file_path+"*.csv"
    csv_file = glob.glob(csv)

    #데이터들을 담을 데이터프레임
    df = pd.DataFrame()
    #통합 데이터 파일의 경로
    total_path = file_path[:-1] + '\\totaldata.csv'

    #통합 데이터 파일이 있는 경우
    if total_path in csv_file:
        #통합 데이터 파일을 읽어옴
        df = pd.read_csv(total_path, encoding='cp949')

        #마지막 저장 날짜 이후의 데이터 확인
        #마지막 저장 날짜 = totaldata의 마지막 데이터의 date
        last = df.tail(1)['date'].values[0]
        last = datetime.strptime(last,"%Y-%m-%d").date()
        diff = datetime.today().date() - last
        temp = last

        #마지막 저장 날짜 이후로 오늘까지 데이터가 존재하는지 확인
        for i in range(diff.days):
            #날짜를 하루씩 증가
            temp = temp + timedelta(days=1)
            #날짜가 temp일 때 파일명
            file_name = file_path[:-1]+'\\data'+str(temp)+'.csv'

            #해당 날짜의 파일이 존재하지 않으면 다음 루프
            if file_name not in csv_file:
                continue

            #존재한다면 csv파일 읽어와서 df에 추가
            t = pd.read_csv(file_name, encoding='cp949')
            df = pd.concat([df, t], ignore_index=True)

    #미리 저장된 파일이 없는 경우
    else:
        #폴더 내의 csv파일에 하나씩 접근
        for i in range(len(csv_file)):
            print(i+1,"/",len(csv_file))
            #csv파일을 읽어와서 df에 추가
            temp = pd.read_csv(csv_file[i], encoding='cp949')
            df = pd.concat([df, temp], ignore_index = True)

    #df의 date열을 datetime으로 형변환
    df['date'] = pd.to_datetime(df['date'])
    #개별 데이터일때 존재하던 인덱스 제거
    df.drop([df.columns[0]], axis=1, inplace=True)
    #통합 데이터 저장
    df.to_csv(total_path, encoding='cp949')
    df.to_sql('vacc',conn)
    cur.execute("select * from vacc")

    #자주 사용하는 데이터를 모아 view생성
    query = """
            create view vacc_occ as
            select date, hospital, max(AZ) as AZ, max(pfizer) as pfizer, max(moderna) as moderna
            from vacc group by date, hospital
            """
    cur.execute(query)

#어제의 백신 발생량
def yesterday_vacc():
    yes = datetime.today().date() - timedelta(days=1)
    #yes = str(yes) + " 00:00:00"
    yes = "2021-08-12 00:00:00"

    query = """
            select sum(AZ+pfizer+moderna), sum(AZ), sum(pfizer), sum(moderna)
            from vacc_occ
            where date = 
            """ + "'"+ yes + "'"

    cur.execute(query)
    yes_result = cur.fetchall()
    #[(잔여백신수량, AZ, pfizer, moderna)]
    yes_vacc = yes_result[0][0]
    yes_AZ = yes_result[0][1]
    yes_pfizer = yes_result[0][2]
    yes_moderna = yes_result[0][3]

    vacc = [yes_AZ, yes_pfizer, yes_moderna]
    labels = ['AZ\n'+str(yes_AZ)+'건', '화이자\n'+str(yes_pfizer)+'건','모더나\n'+str(yes_moderna)+'건']
    explode = [0.05,0.05,0.05]
    colors = ['#4a94b0','#b7e5ff','#d7d7d7']
    wedgeprops = {'width':0.7, 'edgecolor' : 'k', 'linewidth':1}

    plt.pie(vacc,labels = labels, autopct='%.2f%%', explode = explode, colors = colors, wedgeprops = wedgeprops)
    plt.tight_layout()
    plt.show()

#누적 백신 발생량
def acc_vacc():
    yes = datetime.today().date() - timedelta(days=1)
    #yes = str(yes) + " 00:00:00"
    yes = "2021-08-12 00:00:00"

    query = """
            select sum(AZ+pfizer+moderna), sum(AZ), sum(pfizer), sum(moderna)
            from vacc_occ
            """

    cur.execute(query)
    result = cur.fetchall()
    #[(잔여백신수량, AZ, pfizer, moderna)]
    tot_vacc = result[0][0]
    AZ = result[0][1]
    pfizer = result[0][2]
    moderna = result[0][3]

    vacc = [AZ, pfizer, moderna]
    labels = ['AZ\n'+str(AZ)+'건', '화이자\n'+str(pfizer)+'건','모더나\n'+str(moderna)+'건']
    explode = [0.05,0.05,0.05]
    colors = ['#4a94b0','#b7e5ff','#d7d7d7']
    wedgeprops = {'width':0.7, 'edgecolor' : 'k', 'linewidth':1}
    plt.pie(vacc,labels = labels, autopct='%.2f%%', explode = explode, colors = colors, wedgeprops = wedgeprops)
    plt.tight_layout()
    plt.show()

    print("누적",tot_vacc,"건")

#병원별 누적 발생량 - opt : 정렬 단위
#1:전체-전체, 2:전체-일주일, 3:전체-어제, 4:!AZ-전체, 5:!AZ-일주일, 6:!AZ-어제
def hosp_acc(opt):
    yes = datetime.today().date() - timedelta(days=1)
    yes = str(yes) + " 00:00:00"
    #yes = "2021-08-12 00:00:00"
    week = datetime.today().date() - timedelta(weeks = 1)
    week = str(week) + " 00:00:00"
    #week = "2021-08-06 00:00:00"
    month = datetime.today().date() - relativedelta(months = 1)
    month = str(month) + " 00:00:00"
    #month = "2021-07-12 00:00:00"

    #전체-전체
    if opt == 1:
        query = "select hospital, sum(AZ+pfizer+moderna) as tot, count(date) from vacc_occ where AZ+pfizer+moderna != 0 group by hospital order by tot desc"
    #전체-일주일
    elif opt == 2:
        query = "select hospital, sum(AZ+pfizer+moderna) as tot,count(date) from vacc_occ where date between '"+week+"' and '"+yes+"'group by hospital order by tot desc"
    #전체 - 어제
    elif opt == 3:
        query = "select hospital, sum(AZ+pfizer+moderna) as tot,count(date) from vacc_occ where date = '"+yes+"' group by hospital order by tot desc"
    #!AZ - 전체
    elif opt == 4:
        query = "select hospital, sum(pfizer+moderna) as tot, count(date) from vacc_occ group by hospital order by tot desc"
    # !AZ - 일주일
    elif opt == 5:
        query = "select hospital, sum(pfizer+moderna) as tot, count(date) from vacc_occ where date between '" + week + "' and '" + yes + "'group by hospital order by tot desc"
    # !AZ - 어제
    elif opt == 6:
        query = "select hospital, sum(pfizer+moderna) as tot, count(date) from vacc_occ where date = '" + yes + "' group by hospital order by tot desc"

    #쿼리 실행
    cur.execute(query)
    acc = cur.fetchmany(10)

    if not acc:
        print("결과가 없습니다")
        return

    else:
        #병원과 잔여 백신 발생량, 발생 횟수를 저장할 리스트
        hosp = []
        cnt = []
        num = []
        num_show = []

        #쿼리 실행 결과에서 리스트로 데이터 추출
        for i in range(10):
            hosp.append(acc[i][0])
            cnt.append(acc[i][1])
            num.append(acc[i][2])
            num_show.append(acc[i][2] * 4 + 20)

        #시각화
        plt.figure(figsize=(12,4))
        plt.grid(True, axis='y', alpha = 0.5, linestyle='--', color='#d7d7d7')
        plt.bar(hosp, cnt, color=col3, width = 0.4, label='발생량')
        plt.plot(hosp, num_show, color = col7, marker='*', markersize=10,label='발생 횟수')
        plt.tight_layout()

        #횟수 텍스트로 표시
        for i, v in enumerate(hosp):
            plt.text(v, num_show[i]-1, str(num[i])+'회',
                     fontsize = 10, color = col1,
                     horizontalalignment='center',
                     verticalalignment = 'top')

        plt.legend()
        plt.show()

#병원별 평균 발생량 ing
def avg_occ():
    query = """
            select  hospital, sum(AZ+pfizer+moderna) as tot, sum(AZ), sum(pfizer),sum(moderna) 
            from vacc_occ
            group by hospital
            order by tot desc
            """
    cur.execute(query)
    sum = cur.fetchmany(10)

    query = """
            select count(distinct date) from vacc_occ
            """
    cur.execute(query)
    cnt = cur.fetchall()[0][0]

    if not sum:
        print("결과가 없습니다")
        return

    avg_AZ = []
    avg_pfizer = []
    avg_moderna = []
    avg_tot = []
    hosp = []
    for i in range(10):
        hosp.append(sum[i][0])
        avg_tot.append(sum[i][1]/cnt)
        avg_AZ.append(sum[i][2]/cnt)
        avg_pfizer.append(sum[i][3]/cnt)
        avg_moderna.append(sum[i][4]/cnt)

#특정 병원 정렬

#일별 잔여 백신 발생 추이 - 전체, AZ, 화이자, 모더나
def acc_trend():
    #데이터베이스에서 일별 전체 발생량, AZ발생량, 화이자 발생량, 모더나 발생량, 날짜 추출
    query = """
            select sum(AZ+pfizer+moderna) as tot, sum(AZ), sum(pfizer), sum(moderna), date
            from vacc_occ
            group by date
            """
    cur.execute(query)
    trend = cur.fetchall()

    tot = []
    AZ = []
    pfizer = []
    moderna = []
    date = []

    #쿼리문의 결과에 하나씩 접근하여 리스트에 저장
    for i in range(len(trend)):
        tot.append(trend[i][0])
        AZ.append(trend[i][1])
        pfizer.append(trend[i][2])
        moderna.append(trend[i][3])
        date.append(trend[i][4][:-9])

    #시각화
    plt.plot(date, tot, color = col7, marker='*', markersize=10,label='전체 발생량')
    plt.plot(date, AZ, color = col2, marker='o', markersize=5,label='AZ')
    plt.plot(date, pfizer, color = col4, marker='s', markersize=5,label='화이자')
    plt.plot(date, moderna, color = col5, marker='^', markersize=5,label='모더나')
    plt.tight_layout()
    plt.legend()
    plt.show()

#백신 발생 시간대

#시간대별 병원 - 시간대에 백신 데이터가 있으면 cnt > cnt가 많은 순으로

#근처 100개 병원 정보 출력
def show_hosps():
    query = """
            select hospital, hospital_distance, address from vacc
            group by hospital
            """
    cur.execute(query)
    hospital = cur.fetchall()

    query = """
            select sum(AZ+pfizer+moderna) from vacc_occ
            group by hospital
            """
    cur.execute(query)
    total = cur.fetchall()

    column = ["병원명", "거리", "주소", "발생량"]
    df = pd.DataFrame(columns = column)
    df2 = pd.DataFrame(columns = column)
    df3 = pd.DataFrame(columns = column)
    df4 = pd.DataFrame(columns = column)
    cnt = len(hospital)

    for i in range(cnt):
        hosp = hospital[i][0]
        dist = hospital[i][1]
        add = hospital[i][2]
        tot = total[i][0]
        t = cnt/4

        if i<t:
            df.loc[len(df)] = [hosp, dist, add, tot]
        elif i<t*2:
            df2.loc[len(df2)] = [hosp, dist, add, tot]
        elif i<t*3:
            df3.loc[len(df3)] = [hosp, dist, add, tot]
        else:
            df4.loc[len(df4)] = [hosp, dist, add, tot]

    fig = plt.figure(figsize=(12, 4))
    ax = fig.subplots()

    ax.axis('tight')
    ax.axis('off')
    table1 = ax.table(cellText=df.values,
                      colLabels=df.columns,
                      colColours=[col4] * 4,
                      cellLoc='left',
                      colWidths=[0.4, 0.1, 0.4, 0.1],
                      loc="center")

    table2 = ax.table(cellText=df2.values,
                      colLabels=df2.columns,
                      colColours=[col4] * 4,
                      cellLoc='left',
                      colWidths=[0.4, 0.1, 0.4, 0.1],
                      loc="center")

    table3 = ax.table(cellText=df3.values,
                      colLabels=df3.columns,
                      colColours=[col4] * 4,
                      cellLoc='left',
                      colWidths=[0.4, 0.1, 0.4, 0.1],
                      loc="center")

    table4 = ax.table(cellText=df4.values,
                      colLabels=df4.columns,
                      colColours=[col4] * 4,
                      cellLoc='left',
                      colWidths=[0.4, 0.1, 0.4, 0.1],
                      loc="center")

    table1.auto_set_font_size(False)
    table1.set_fontsize(12)
    table1.scale(1,1.2)
    table2.auto_set_font_size(False)
    table2.set_fontsize(12)
    table2.scale(1, 1.2)
    table3.auto_set_font_size(False)
    table3.set_fontsize(12)
    table3.scale(1, 1.2)
    table4.auto_set_font_size(False)
    table4.set_fontsize(12)
    table4.scale(1, 1.2)

    table2.set_visible(False)
    table3.set_visible(False)
    table4.set_visible(False)

    labels = ('1','2','3','4')
    tables = [table1,table2,table3,table4]

    def func(label):
        idx = labels.index(label)
        if idx == 0:
            tables[0].set_visible(True)
            tables[1].set_visible(False)
            tables[2].set_visible(False)
            tables[3].set_visible(False)
        elif idx == 1:
            tables[0].set_visible(False)
            tables[1].set_visible(True)
            tables[2].set_visible(False)
            tables[3].set_visible(False)
        elif idx == 2:
            tables[0].set_visible(False)
            tables[1].set_visible(False)
            tables[2].set_visible(True)
            tables[3].set_visible(False)
        else:
            tables[0].set_visible(False)
            tables[1].set_visible(False)
            tables[2].set_visible(False)
            tables[3].set_visible(True)
        fig.canvas.draw()

    axes  = plt.axes([0.02, 0.35, 0.08, 0.2])
    radio = pwd.RadioButtons(axes, labels,activecolor=col2)
    radio.on_clicked(func)

    plt.show()

get_files(file_path)
#yesterday_vacc()
#hosp_acc(1)
#acc_vacc()
#avg_occ()
#acc_trend()
show_hosps()