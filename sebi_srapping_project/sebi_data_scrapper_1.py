import requests
from bs4 import BeautifulSoup
import pandas as pd
from requests.adapters import Retry, HTTPAdapter
payload = {
    'currdate': '',
    'loginflag': '0',
    'searchValue': '',
    'pmrId': '',
    'year': '',
    'month': '',
    'org.apache.struts.taglib.html.TOKEN': '...',
    'loginEmail': '',
    'loginPassword': '',
    'cap_login': '',
    'moduleNo': '-1',
    'moduleId': '',
    'link': '',
    'yourName': '',
    'friendName': '',
    'friendEmail': '',
    'mailmessage': '',
    'cap_email': ''
}
headers = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "en-US,en;q=0.9",
    "Cache-Control": "max-age=0",
    "Connection": "keep-alive",
    "Host": "www.sebi.gov.in",
    "Origin": "https://www.sebi.gov.in",
    "Referer": "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes",
    "User-Agent": "Mozilla/5.0 (Linux; Android 6.0; Nexus 5 Build/MRA58N) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/114.0.0.0 Mobile Safari/537.36"
}

def get_session_with_retries(retries=5, backoff_factor=0.2, session=None, allowed_methods=["POST","GET"]):
    if session is None:
        session = requests.Session()

    retry_strategy = Retry(
        total=retries,
        backoff_factor=backoff_factor,
        status_forcelist=[500, 502, 503, 504],
        allowed_methods=allowed_methods
    )
    
    adapter = HTTPAdapter(max_retries=retry_strategy)
    session.mount('http://', adapter)
    session.mount('https://', adapter)
    
    return session
class PortfolioManagerPerformance:
    def __init__(self):
        self.url = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes"
        portfolio_managers_month_year=self.get_portfolio_managers_month_year(self.url)
        
        self.years = portfolio_managers_month_year[2]
        self.months = portfolio_managers_month_year[1]

        # apllied check for years
        year = input("Enter year: ")
        while True:
            if year in self.years:
                break
            else:
                year = input("wrong input! Enter year again: ")
        self.year = year
        
        # apllied check for months
        month = input("Enter month start with capital letter: ")
        while True:
            if month in self.months:
                break
            else:
                month = input("wrong input! Enter month start with capital letter: again: ")
        self.month = month
        self.manager_names_list = portfolio_managers_month_year[0]
        self.managers_data = []
        self.performance_table_data = []
        self.overall_performance_data = []
    # below function will take url as input and returns the list containing  list of names of all portfolio managers available and list of months and list of years option available 
    def get_portfolio_managers_month_year(self,url):
        session = get_session_with_retries(3)
        response = session.get(url,params={'doPmr': 'yes'},timeout=10)
        soup = BeautifulSoup(response.content, "lxml")
        managers_month_years_available=[]
        options = soup.find("select", attrs={'name':"pmrId", 'class':"f_control"}).find_all("option")
        #  all portfolio managers names are stored in portfolio_managers from index 1 0th index element is a select Notation 
        portfolio_managers = [{option.text:option.get("value")} for option in options[1:]]
        managers_month_years_available.append(portfolio_managers)
        # for months option available
        options = soup.find("select", attrs={"name": "month", 'class':"f_control"}).find_all("option")
        #  all months are stored in months from index 1
        month = {option.text:option.get("value") for option in options[1:]}
        managers_month_years_available.append(month)
        # for years option available
        options = soup.find("select", attrs={"name": "year", 'class':"f_control"}).find_all("option")
        #  all years are stored in years from index 1
        years = [option.text for option in options[1:]]
        managers_month_years_available.append(years)
        return managers_month_years_available
    
    """
    below function that takes manager_name and collection all tables in html form and returns list containing manager name l and
    Total Assets under Management (AUM) as on last day of the month (Amount in INR crores) isted in the first table
    """
    def get_manager_data(self,manager_name,table_one):
            # try except block for extracting managers name and the Total Assets under Management (AUM)
            try:
                # desired table 1
                # can read html as a pandas dataframe if it is in string form
                # reading html as pandas dataframe
                table_one = pd.read_html(str(table_one))[0]
                #manager name present in the table
                manager_name=table_one.columns[1][0]
                # Total Assets under Management (AUM) 
                AUM=table_one.columns[1][-1]
            except:
                # if data not available for a particular manager performing below operations for keeping shape of dataframe same for all dataframes
                AUM=' '
            return [manager_name,AUM]
    """
    below function will take collection all tables in html form reads the desired table from collection of table and returns  a dictionary
    containing strategy and benchmark details
    i.e {"strategy 1 name":'abc',"strategy 1 AUM": 25,"Strategy 1 Returns (% 1 month)" : 3.4,'Strategy 1 Returns (% 1 year)': 2.21,
        "Strategy 1 Turnover (% 1 month)":3.4,'Strategy 1 Turnover (% 1 year)':2.01,
        'Benchmark 1 Name':'cde','Benchmark 1 Returns (% 1 month)' : 0.21 ,'Benchmark 1 Returns (% 1 year)': 4.3,"strategy 2 name.....
        .....................}
    """
    def get_performance_data(self,table_nine): 
        # try except block for extracting perfromace data
        try:
            # desiered table 9(8 in index)
            # reading html as pandas dataframe
            table_nine = pd.read_html(str(table_nine))[0] 
            performance_data_values = []
            performance_data_keys = []
            # filling the NAN value with "0" for better readbility of the table values
            table_nine = table_nine.fillna('0')
            """
            looping through the performance table and extracting desired values
            number of times first loop will iterate will be equal to the number of rows in the table we will not consider last row as it's a total value so its not in our count
            """
            # the below value will update the keys which we want to make as column names in performance dataframe 
            strategy_count=1
            # i is count of rows
            if table_nine.shape[0]%2==1:
                row_count=table_nine.shape[0]-1
            else:
                row_count=table_nine.shape[0]-2
            for i in range(row_count):
                """
                below 'if' is for extracting the strategy name and data related to this
                this if will run only when index number i is like 0,2,4,6,8......
                below performance_data_keys will be column names as we wanted in our performance dataframe
                inceasing strategy_count as encounter a new strategy
                """
                if i%2==0:
                    performance_data_keys.extend(['Strategy '+ str(strategy_count)+ ' Name','Strategy '+ str(strategy_count)+ ' AUM (in cr)','Strategy '+ str(strategy_count)+ ' Returns (% 1 month)','Strategy '+ str(strategy_count)+ ' Returns (% 1 year)'
                             ,'Strategy '+ str(strategy_count)+ ' Turnover (% 1 month)','Strategy '+ str(strategy_count)+ ' Turnover (% 1 year)','Benchmark '+ str(strategy_count)+ ' Name'
                             ,'Benchmark '+ str(strategy_count)+ ' Returns (% 1 month)','Benchmark '+ str(strategy_count)+ ' Returns (% 1 year)'])
                    strategy_count+=1
                    """
                    below for loop will iterate through all the columns in the table for alternate rows indexed i.e 0,2,4,6,8....
                    this is for the strategies 
                    """
                    for j in range(table_nine.shape[1]):
                        if table_nine.loc[i][j]!='0':
                            performance_data_values.append(table_nine.loc[i][j])
                        else:
                            performance_data_values.append(' ')

                    """
                    below else is for extracting the benchmark name of the strategies and data related to this
                    below else will run for rows indexed i.e. 1,3,5,7
                    there are only three values inthe row which we want to extract are on the position 0 2 and 3rd
                    """
                else :
                    if table_nine.loc[i][0] != '0':
                        performance_data_values.extend([table_nine.loc[i][0],table_nine.loc[i][2],table_nine.loc[i][3]])
                        # if strategy is there but bench mark is not present then we add space in place of benchmark name to keep further extraction in correct order
                    else:
                        performance_data_values.extend([" ",table_nine.loc[i][2],table_nine.loc[i][3]])
            performance_data_dict_one_manager=dict(zip(performance_data_keys, performance_data_values))
        except:
            # if data not available for a particular manager performing below operations for keeping shape of dataframe same for all dataframes
            performance_data_dict_one_manager=dict(zip(['Strategy 1 Name'], [' ']))
        return performance_data_dict_one_manager

    """
    [Strategy 1 Name,Strategy 1 AUM (in cr),Strategy 1 Returns (% 1 month),Strategy 1 Returns (% 1 year),Strategy 1 Turnover (% 1 month),
    Strategy 1 Turnover (% 1 year),Benchmark 1 Name,Benchmark 1 Returns (% 1 month),Benchmark 1 Returns (% 1 year)]
    ['2POINT2 Long Term Value Fund', 674.42, -2.76, 27.51, 0.08, 0.88, 'NSE NIFTY 500_TRI', -0.48, 33.44]
    below function takes  strategy information list(i.e. ['2POINT2 Long Term Value Fund', 674.42, -2.76, 27.51, 0.08, 0.88, 'NSE NIFTY 500_TRI', -0.48, 33.44]) 
    as input and returns list of few the weighted average values which we call the overall performance
    """                
    def get_overall_performance(self,startegies_benchmark_details):  
        """
        creating a variable named overall performace which will conatain four types of  weighted averages 
        which we call overall performance
        'Overall Strategy Returns (1M)','Overall Strategy Returns (1Y)','Overall Benchmark Returns (1M)',
        'Overall Benchmark Returns (1Y)'
        """
        overall_performance_one_manager = [" "] * 4
        try:
            total_aum_sum=0
            weighted_sum_strategy_one_month_returns=0
            weighted_sum_strategy_one_year_returns=0
            weighted_sum_benchmark_one_month_returns=0
            weighted_sum_benchmark_one_year_returns=0
            for i in range(1,len(startegies_benchmark_details),9):
                # calculating total Strategy Aum sum for the calculation of weighted averages
                total_aum_sum+=startegies_benchmark_details[i]
                # 1 month strategy returns is on 1 sth postion from strategy AUM
                weighted_sum_strategy_one_month_returns+=startegies_benchmark_details[i]*startegies_benchmark_details[i+1]

                # 1 year strategy returns  is on 2 sth postion from strategy AUM
                weighted_sum_strategy_one_year_returns+=startegies_benchmark_details[i]*startegies_benchmark_details[i+2]

                # 1 month benchmark returns is on 6th postion from strategy AUM
                weighted_sum_benchmark_one_month_returns+=startegies_benchmark_details[i]*startegies_benchmark_details[i+6]

                # 1 year benchmark returns is on 7th postion from strategy AUM
                weighted_sum_benchmark_one_year_returns+=startegies_benchmark_details[i]*startegies_benchmark_details[i+7]

                # assigning weighted averages of 1 month,1 year returns of strategy and benchmark to variable 'overall performance'
                # weigted average = weighted_sum / totat_aum_sum
                overall_performance_one_manager=[weighted_sum_strategy_one_month_returns/total_aum_sum,weighted_sum_strategy_one_year_returns/total_aum_sum,
                        weighted_sum_benchmark_one_month_returns/total_aum_sum,weighted_sum_benchmark_one_year_returns/total_aum_sum
                    ]
        except:
            pass
        return overall_performance_one_manager

    def main(self):
        for manager in self.manager_names_list:
            payload['pmrId']=list(manager.values())[0]
            payload['year'] = self.year
            payload['month'] = self.months[self.month]
            session = get_session_with_retries()
            response = session.post( self.url,headers=headers, params = {'doPmr': 'yes'}, data=payload)
            soup=BeautifulSoup(response.content,'lxml')
            tables =soup.find_all('table')
            if tables:
                one_manager_detail = self.get_manager_data(list(manager.keys())[0], tables[0])
                self.managers_data.append(one_manager_detail)
                performance_table_detail_one_manager = self.get_performance_data(tables[8])
                self.performance_table_data.append(performance_table_detail_one_manager)
            else:
                one_manager_detail = [list(manager.keys())[0],' ']
                self.managers_data.append(one_manager_detail)
                performance_table_detail_one_manager = dict(zip(['Strategy 1 Name'], [' ']))
                self.performance_table_data.append(performance_table_detail_one_manager)
            overall_performance_details_one_manager = self.get_overall_performance(list(performance_table_detail_one_manager.values()))
            self.overall_performance_data.append(overall_performance_details_one_manager)
            print("one_manager_detail : ",one_manager_detail)
            if one_manager_detail[1]!=" ":
                print("performance_table_detail_one_manager : ",list(performance_table_detail_one_manager.values())) 
                print("overall_performance_details_one_manager : ",overall_performance_details_one_manager)
            else:
                print(one_manager_detail[0] ," : No records available")
            print("                                                           ")
            print("                                                           ")
        self.managers_data = pd.DataFrame(self.managers_data, columns=['Name of the Portfolio Manager',
                        "Total Assets under Management (AUM) as on last day of the month (Amount in INR crores)"])
        self.overall_performance_data = pd.DataFrame(self.overall_performance_data, columns=['Overall Strategy Returns (1M)','Overall Strategy Returns (1Y)',
                                                                               'Overall Benchmark Returns (1M)','Overall Benchmark Returns (1Y)'])
        self.performance_table_data = pd.DataFrame(self.performance_table_data)
        df = pd.concat([self.managers_data, self.overall_performance_data, self.performance_table_data], axis=1)
        # storing into a csv file with file name containing year and month name
        df.to_csv(self.month + "_" + self.year + '_performance.csv', index=False)
data=PortfolioManagerPerformance()
data.main()
