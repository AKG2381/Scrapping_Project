import requests
from bs4 import BeautifulSoup
import pandas as pd
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class PortfolioManagerPerformance:
    def __init__(self):
        self.url = "https://www.sebi.gov.in/sebiweb/other/OtherAction.do?doPmr=yes"
        self.years,self.months,self.manager_names_list = self.get_years_month_portfolio_managers_data(self.url)

        # applied check for years
        year = input("Enter year: ")
        while True:
            if year in self.years:
                break
            else:
                year = input("wrong input! Enter year again: ")
        self.year = year

        # applied check for months
        month = input("Enter month start with capital letter: ")
        while True:
            if month in self.months:
                break
            else:
                month = input("wrong input! Enter month start with capital letter: again: ")
        self.month = month
        self.managers_data = []
        self.performance_table_data = []
        self.overall_performance_data = []
 
    # below function will take url as input and returns the list of years,months and names of all portfolio managers  available
    @staticmethod
    def get_years_month_portfolio_managers_data(url):
        
        
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        # years
        year_options = soup.find("select", attrs={"name": "year"}).find_all("option")
        years = [option.text for option in year_options][1:]

        # months 
        month_options = soup.find("select", attrs={"name": "month"}).find_all("option")
        month = [option.text for option in month_options][1:]

        # managers
        portfolio_managers_options = soup.find("select", attrs={"name": "pmrId"}).find_all("option")
        portfolio_managers = list(set([option.text for option in portfolio_managers_options][1:]))
            
        return years,month,portfolio_managers

    # below  function that takes manager_name,year, month,driver as inout and  triggers the javascript "Go" button and
    # returns collection all tables in html form
    @staticmethod
    def trigger_button(manager_name, year, month, driver, url):
        # Navigate to the website
        try:
            driver.get(url)

            # Fill the form data
            wait = WebDriverWait(driver, 5)  # Set the explicit wait timeout to 5 seconds
            pmr_id_input = wait.until(EC.presence_of_element_located((By.NAME, 'pmrId')))
            pmr_id_input.send_keys(manager_name)

            year_input = driver.find_element(By.NAME, 'year')
            year_input.send_keys(year)

            month_input = driver.find_element(By.NAME, 'month')
            month_input.send_keys(month)

            # click the JavaScript trigger 'GO' button
            driver.execute_script("getPMR();")

            # Wait for the page to load and the search results to be available
            wait.until(EC.presence_of_element_located((By.TAG_NAME, 'table')))
            # Parse the HTML content
            soup = BeautifulSoup(driver.page_source, "html.parser")
            # Find the table containing the search results
            tables = soup.find_all("table")
            return tables
        except:
            return None

    """
    below function that takes manager_name and collection all tables in html form and returns list containing manager
     name and Total Assets under Management (AUM) as on last day of the month (Amount in INR crores) listed in the first
    table
    """

    @staticmethod
    def get_manager_data(manager_name, tables):
        # try except block for extracting managers name and the Total Assets under Management (AUM)
        try:
            # desired table 1
            # can read html as a pandas dataframe if it is in string form
            table_one = str(tables[0])
            # reading html as pandas dataframe
            table_one = pd.read_html(table_one)[0]

            # manager name present in the table
            manager_name = table_one.columns[1][0]

            # Total Assets under Management (AUM)
            aum = table_one.columns[1][-1]

        except:
            # if data not available for a particular manager performing below operations for keeping shape of
            # dataframe same for all dataframes
            aum = ' '
        return [manager_name, aum]

    """
    below function will take collection all tables in html form reads the desired table from collection of table and 
    returns  a dictionary containing strategy and benchmark details

    i.e {"strategy 1 name":'abc',"strategy 1 AUM": 25,"Strategy 1 Returns (% 1 month)" : 3.4,'Strategy 1 Returns
     (% 1 year)': 2.21,"Strategy 1 Turnover (% 1 month)":3.4,'Strategy 1 Turnover (% 1 year)':2.01,'Benchmark 1 Name':
     'cde','Benchmark 1 Returns (% 1 month)' : 0.21 ,'Benchmark 1 Returns (% 1 year)': 4.3,"strategy 2 name.....
        .....................}

    """

    @staticmethod
    def get_performance_data(tables):
        # try except block for extracting performance data
        try:
            # desired table 9(8 in index)
            # reading html as pandas dataframe
            table_nine = str(tables[8])
            table_nine = pd.read_html(table_nine)[0]
            performance_data_values = []
            performance_data_keys = []

            # filling the NAN value with "0" for better readability of the table values
            table_nine = table_nine.fillna('0')

            """
            looping through the performance table and extracting desired values
            number of times first loop will iterate will be equal to the number of rows in the table we will not 
            consider last row as it's a total value so its not in our count
            """
            # the below value will update the keys which we want to make as column names in performance dataframe 
            strategy_count = 1

            if table_nine.shape[0] % 2 == 1:
                row_count = table_nine.shape[0] - 1
            else:
                row_count = table_nine.shape[0] - 2
            # i is count of rows
            for i in range(row_count):
                """
                below 'if' is for extracting the strategy name and data related to this
                this if will run only when index number i is like 0,2,4,6,8......
                below performance_data_keys will be column names as we wanted in our performance dataframe
                increasing strategy_count as encounter a new strategy
                """
                if i % 2 == 0:
                    performance_data_keys.extend(['Strategy ' + str(strategy_count) + ' Name',
                                                  'Strategy ' + str(strategy_count) + ' AUM (in cr)',
                                                  'Strategy ' + str(strategy_count) + ' Returns (% 1 month)',
                                                  'Strategy ' + str(strategy_count) + ' Returns (% 1 year)',
                                                  'Strategy ' + str(strategy_count) + ' Turnover (% 1 month)',
                                                  'Strategy ' + str(strategy_count) + ' Turnover (% 1 year)',
                                                  'Benchmark ' + str(strategy_count) + ' Name',
                                                  'Benchmark ' + str(strategy_count) + ' Returns (% 1 month)',
                                                  'Benchmark ' + str(strategy_count) + ' Returns (% 1 year)'])
                    strategy_count += 1

                    """
                    below for loop will iterate through all the columns in the table for alternate rows indexed i.e 0,2,
                    4,6,8....
                    this is for the strategies 
                    """
                    for j in range(table_nine.shape[1]):
                        if table_nine.loc[i][j] != '0':
                            performance_data_values.append(table_nine.loc[i][j])
                        else:
                            performance_data_values.append(' ')

                    """
                    below else is for extracting the benchmark name of the strategies and data related to this
                    below else will run for rows indexed i.e. 1,3,5,7
                    there are only three values in the row which we want to extract are on the position 0 2 and 3rd
                    """
                else:
                    if table_nine.loc[i][0] != '0':
                        performance_data_values.extend(
                            [table_nine.loc[i][0], table_nine.loc[i][2], table_nine.loc[i][3]])

                        # if strategy is there but benchmark is not present then we add space in place of benchmark
                        # name to keep further extraction in correct order
                    else:
                        performance_data_values.extend([" ", table_nine.loc[i][2], table_nine.loc[i][3]])

            performance_data_dict_one_manager = dict(zip(performance_data_keys, performance_data_values))
        except:
            # if data not available for a particular manager performing below operations for keeping shape of
            # dataframe same for all dataframes
            performance_data_dict_one_manager = dict(zip(['Strategy 1 Name'], [' ']))
        return performance_data_dict_one_manager

    """

    [Strategy 1 Name,Strategy 1 AUM (in cr),Strategy 1 Returns (% 1 month),Strategy 1 Returns (% 1 year),Strategy 1 
    Turnover (% 1 month),Strategy 1 Turnover (% 1 year),Benchmark 1 Name,Benchmark 1 Returns (% 1 month),Benchmark 1 
    Returns (% 1 year)]
    ['2POINT2 Long Term Value Fund', 674.42, -2.76, 27.51, 0.08, 0.88, 'NSE NIFTY 500_TRI', -0.48, 33.44]
    below function takes  strategy information list(i.e. ['2POINT2 Long Term Value Fund', 674.42, -2.76, 27.51, 0.08, 
    0.88, 'NSE NIFTY 500_TRI', -0.48, 33.44]) 
    as input and returns list of few the weighted average values which we call the overall performance
    """

    @staticmethod
    def get_overall_performance(strategies_benchmark_details):
        """
        creating a variable named overall performance which will contain four types of  weighted averages
        which we call overall performance
        'Overall Strategy Returns (1M)','Overall Strategy Returns (1Y)','Overall Benchmark Returns (1M)',
        'Overall Benchmark Returns (1Y)'

        and one more values will be there named Total Discretionary AUM
        """
        overall_performance_one_manager = [" "] * 5
        try:
            total_aum_sum = 0
            weighted_sum_strategy_one_month_returns = 0
            weighted_sum_strategy_one_year_returns = 0
            weighted_sum_benchmark_one_month_returns = 0
            weighted_sum_benchmark_one_year_returns = 0
            for i in range(1, len(strategies_benchmark_details), 9):
                # calculating total Strategy Aum sum for the calculation of weighted averages
                total_aum_sum += strategies_benchmark_details[i]
                # 1 month strategy returns is on 1 sth position from strategy AUM
                weighted_sum_strategy_one_month_returns += strategies_benchmark_details[i] * \
                                                           strategies_benchmark_details[i + 1]

                # 1 year strategy returns  is on 2 sth position from strategy AUM
                weighted_sum_strategy_one_year_returns += strategies_benchmark_details[i] * \
                                                          strategies_benchmark_details[i + 2]

                # 1 month benchmark returns is on 6th position from strategy AUM
                weighted_sum_benchmark_one_month_returns += strategies_benchmark_details[i] * \
                                                            strategies_benchmark_details[i + 6]

                # 1 year benchmark returns is on 7th position from strategy AUM
                weighted_sum_benchmark_one_year_returns += strategies_benchmark_details[i] * \
                                                           strategies_benchmark_details[i + 7]

                # assigning weighted averages of 1 month,1 year returns of strategy and benchmark to variable
                # 'overall performance' weighted average = weighted_sum / total_aum_sum
                overall_performance_one_manager = [
                    weighted_sum_strategy_one_month_returns / total_aum_sum,
                    weighted_sum_strategy_one_year_returns / total_aum_sum,
                    weighted_sum_benchmark_one_month_returns / total_aum_sum,
                    weighted_sum_benchmark_one_year_returns / total_aum_sum,
                    total_aum_sum
                ]
        except:
            pass
        return overall_performance_one_manager

    def main(self):
        # Initialize the webdriver          
        options = webdriver.ChromeOptions()
        options.add_argument("--headless")
        options.add_argument("--silent")
        options.add_argument("--log-level=3")
        driver = webdriver.Chrome(options=options)

        for manager in self.manager_names_list[::]:
            tables = self.trigger_button(manager, self.year, self.month, driver, self.url)

            one_manager_detail = self.get_manager_data(manager, tables)

            self.managers_data.append(one_manager_detail)

            performance_table_detail_one_manager = self.get_performance_data(tables)

            self.performance_table_data.append(performance_table_detail_one_manager)

            overall_performance_details_one_manager = self.get_overall_performance(
                list(performance_table_detail_one_manager.values()))

            self.overall_performance_data.append(overall_performance_details_one_manager)

            print("one_manager_detail : ", one_manager_detail)
            if one_manager_detail[1] != " ":
                print("performance_table_detail_one_manager : ", list(performance_table_detail_one_manager.values()))
                print("overall_performance_details_one_manager : ", overall_performance_details_one_manager)
            else:
                print(one_manager_detail[0], " : No records available")
            print("                                                           ")
            print("                                                           ")

        self.managers_data = pd.DataFrame(self.managers_data, columns=['Name of the Portfolio Manager',
                                                                        "Total Assets under Management (AUM) as on last day of the month (Amount in INR crores)"])

        self.overall_performance_data = pd.DataFrame(self.overall_performance_data,
                                                     columns=['Overall Strategy Returns (1M)',
                                                              'Overall Strategy Returns (1Y)',
                                                              'Overall Benchmark Returns (1M)',
                                                              'Overall Benchmark Returns (1Y)',
                                                              'Total AUM (Discretionary)'])
        self.performance_table_data = pd.DataFrame(self.performance_table_data)

        df = pd.concat([self.managers_data, self.overall_performance_data, self.performance_table_data], axis=1)
        # storing into a csv file with file name containing year and month name
        df.to_csv(self.month + "_" + self.year + '_performance.csv', index=False)

data = PortfolioManagerPerformance()
data.main()
