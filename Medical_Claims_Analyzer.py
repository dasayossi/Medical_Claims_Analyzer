import numpy as np
import pandas as pd
from logging import Logger
import json


class Medical_claims_Analyzer:

    def __init__(self):

        self.logger = Logger('Medical_claims_Analyzer')
        self.inpatient = pd.read_csv('inpatient.csv')
        self.outpatient = pd.read_csv('outpatient.csv')

        with open('chronic_conditions.json', 'r') as openfile:
            # Reading chronic conditions from json file
            chronic_conditions = json.load(openfile)
            self.chronic_conditions_arr_dic = {}
            for key, diagnoses_list in chronic_conditions.items():
                self.chronic_conditions_arr_dic[key] = np.array(diagnoses_list)

        self.inpatient_diagnoses_keys = [key for key in self.inpatient.keys() if 'ICD9_DGNS_CD_' in key]
        self.outpatient_diagnoses_keys = [key for key in self.outpatient.keys() if 'ICD9_DGNS_CD_' in key]
        self.chronic_conditions_database = pd.DataFrame(self.get_empty_chronic_dict())

    def get_diagnoses_by_id(self, id_):

        diagnos_list = np.array([])
        inpatient_by_id = self.inpatient[self.inpatient['DESYNPUF_ID'] == id_]

        for diagnos in self.inpatient_diagnoses_keys:
            diagnos_list = np.append(diagnos_list, inpatient_by_id[diagnos].to_numpy())

        outpatient_by_id = self.outpatient[self.outpatient['DESYNPUF_ID'] == id_]

        for diagnos in self.outpatient_diagnoses_keys:
            diagnos_list = np.append(diagnos_list, outpatient_by_id[diagnos].to_numpy())

        return diagnos_list

    def get_empty_chronic_dict(self):
        chronic_dict = {'ID': []}
        for key in self.chronic_conditions_arr_dic.keys():
            chronic_dict[key] = []

        return chronic_dict

    def get_chronic_condition_data(self, ids_list):

        existing_chronic_conditions = pd.DataFrame(self.get_empty_chronic_dict())
        chronic_dict = self.get_empty_chronic_dict()
        for id_ in ids_list:

            id_chronic_conditions = self.chronic_conditions_database[self.chronic_conditions_database['ID'] == id_]
            if len(id_chronic_conditions) == 1:
                self.logger.info(f"{id_} Already exist in database")
                existing_chronic_conditions = existing_chronic_conditions.append(id_chronic_conditions)
                continue

            chronic_dict['ID'].append(id_)
            diagnos_list = self.get_diagnoses_by_id(id_)

            for key, diagnoses_list in self.chronic_conditions_arr_dic.items():
                if pd.Series(diagnos_list).isin(diagnoses_list).any():

                    # patient has this condition
                    chronic_dict[key].append(1)
                else:

                    chronic_dict[key].append(0)

        new_chronic_conditions = pd.DataFrame(chronic_dict)

        # Adding the new results to the database 
        self.chronic_conditions_database = self.chronic_conditions_database.append(new_chronic_conditions)

        # return merged DataFrame, existing results and the new results
        return new_chronic_conditions.append(existing_chronic_conditions)

    def get_total_charges_by_id(self, id_, year):

        total_charge = 0
        inpatient_by_id = self.inpatient[self.inpatient['DESYNPUF_ID'] == id_]

        for index, date in inpatient_by_id['CLM_FROM_DT'].items():
            try:
                if int(date / 10000) == year:
                    total_charge += inpatient_by_id['CLM_PMT_AMT'].get(index)
            except:
                self.logger.warn(f"{id_} has corrapted date")

        outpatient_by_id = self.outpatient[self.outpatient['DESYNPUF_ID'] == id_]
        for index, date in outpatient_by_id['CLM_FROM_DT'].items():
            try:
                if int(date / 10000) == year:
                    total_charge += outpatient_by_id['CLM_PMT_AMT'].get(index)
            except:
                self.logger.warn(f"{id_} has corrapted date")

        return total_charge

    def get_total_charges(self, ids_list, year):
        total_charges_dic = {'ID': [], 'total_chatges': []}
        for id_ in ids_list:
            total_charges_dic['ID'].append(id_)
            total_charges_dic['total_chatges'].append(self.get_total_charges_by_id(id_, year))

        return pd.DataFrame(total_charges_dic)


if __name__ == '__main__':
    ############## Test ###############

    analyzer = Medical_claims_Analyzer()

    list_of_id_for_test1 = ['0013E139F1F37264', '000308435E3E5B76']
    list_of_id_for_test2 = ['0013E139F1F37264aaa', '000308435E3E5B76', '001EA2F4DB30F105', '0004F0ABD505251D']

    res1 = analyzer.get_chronic_condition_data(list_of_id_for_test1)
    res2 = analyzer.get_chronic_condition_data(list_of_id_for_test2)

    total_charge_1 = analyzer.get_total_charges(list_of_id_for_test1, 2009)
    total_charge_1_2 = analyzer.get_total_charges(list_of_id_for_test1, 2010)

    total_charge_2 = analyzer.get_total_charges(list_of_id_for_test2, 2009)
    total_charge_2_2 = analyzer.get_total_charges(list_of_id_for_test2, 2010)
