import pythoncivicrm

import server_settings

class CiviCRMUtils:
    civi_timeout = server_settings.CIVICRM_TIME_OUT
    
    def get_case_id(self, report_id):
        """
        given report id, it search for the associated case

        Args:
        report_id the report_id of the case we are searching for
        
        Returns:
        case entity_id for adding activites etc.
        """
        if not report_id:
            raise RuntimeError("report id is not provided")
        url = server_settings.CIVICRM_REST_SERVER + server_settings.CIVICRM_REST_API_URL
        civicrm = pythoncivicrm.CiviCRM(url, server_settings.CIVICRM_SITE_KEY, server_settings.CIVICRM_API_KEY, timeout=self.civi_timeout, use_ssl=True)
        try:
            report_case =  civicrm.get("case",
                                custom_7 = report_id)
        except requests.exceptions.ConnectionError as e:
            logger.warning("unable to retrieve the report from civicrm database: " + e)
            raise RuntimeError("unable to retrieve the report from civicrm database: " + e)

        if (len(report_case)==0):
            return None
        else:
            return report_case[0]['id']

    def get_activity_id(self, case_db_id):
        """
        given case id, it search for the activity id associated to opening the case

        Args:
        case_id the id of the case in civicrm db
        
        Returns:
        activity entity_id for adding activites etc.
        """
        url = server_settings.CIVICRM_REST_SERVER + server_settings.CIVICRM_REST_API_URL
        civicrm = pythoncivicrm.CiviCRM(url, server_settings.CIVICRM_SITE_KEY, server_settings.CIVICRM_API_KEY, timeout=self.civi_timeout, use_ssl=True)
        try:
            case_activities =  civicrm.get("activity", case_id = case_db_id)

        except requests.exceptions.ConnectionError as e:
            logger.warning("unable to locate the report submission associated with the attachment: " + e)
            raise RuntimeError("unable to locate the report submission associated with the attachment: " + e.message)

        if (len(case_activities)==0):
            return None
        else:
            return case_activities[0]['id']
