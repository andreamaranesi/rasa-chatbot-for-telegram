from typing import Text, List, Any, Dict, Union

from rasa_sdk import Tracker, FormValidationAction, Action
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.types import DomainDict
from rasa_sdk.events import SlotSet, UserUtteranceReverted,FollowupAction


import pandas as pd


class SingletonReadingCsv:
    """this classe uses Singleton pattern to read once the restaurant csv file"""

    __csv = None

    @staticmethod
    def get_csv():
        if SingletonReadingCsv.__csv is None:
            SingletonReadingCsv.__csv = pd.read_csv(
                "restaurant_week_2018_final.csv")

        return SingletonReadingCsv.__csv


class ValidatRestaurantNameForm(FormValidationAction):
    """this classe validates the restaurant name the user provides 
    the restaurant name must be in the last restaurant list"""

    def name(self) -> Text:
        return "validate_form_restaurant_name"

    @staticmethod
    def check_restaurant_name(restaurant_name: str, tracker):
        last_list = ReadRestaurantList.read_list(tracker)

        if not last_list:
            return ""

        restaurant_name = restaurant_name.lower()

        for name in last_list.keys():
            name_lower = name.lower()
            if restaurant_name in name_lower or name_lower in restaurant_name:
                return name

        return None

    async def extract_restaurant_name(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        slot_value = SearchEntities.return_last_entity(
            tracker, "restaurant_name")

        if slot_value is not None:
            return {"restaurant_name": slot_value}

        return {}

    def validate_restaurant_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if slot_value is not None:
            print("sarching in the loop the restaurant  " + slot_value)

            restaurant_name = ValidatRestaurantNameForm.check_restaurant_name(
                slot_value, tracker)

            if restaurant_name is not None:
                return {"restaurant_name": restaurant_name}

        dispatcher.utter_message(
            text=f" I need a restaurant name that is in the LAST given restaurant list.")

        return {"restaurant_name": None}


class ValidateNameForm(FormValidationAction):
    """this classe validates the restaurant type (italian, japanese etc..) the user provides 
    the restaurant type must be in the restaurant csv"""

    def name(self) -> Text:
        return "validate_form_restaurant_type"

    async def extract_restaurant_type(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        slot_value = SearchEntities.return_last_entity(
            tracker, "restaurant_type")

        if slot_value is not None:
            return {"restaurant_type": slot_value}

        return {}

    # check if the restaurant type is present in the dataset
    @staticmethod
    def check_restaurant_type(restaurant_type: str):
        df = SingletonReadingCsv.get_csv()
        category_values = df['restaurant_type'].str.lower().values
        category_values_dict = {value: True for value in category_values}

        if restaurant_type.lower() not in category_values_dict:
            return False
        return True


    def validate_restaurant_type(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        print("restaurant type form")

        if slot_value is not None:
            if ValidateNameForm.check_restaurant_type(slot_value):
                dispatcher.utter_message(
                    text="Ok great, " + slot_value + " restaurant type will be searched!")
                return {"restaurant_type": slot_value}
            else:
                dispatcher.utter_message(
                    text=f" I'm assuming you mis-spelled the restaurant type.")

        dispatcher.utter_message(
            text=f" I need to ask the restaurant type.")
        return {"restaurant_type": None}


class SearchEntities:
    """searches entities from the latest message"""

    @staticmethod
    def return_last_entity(tracker, entity, all_results=False):
        entities = tracker.latest_message["entities"]
       # print(entities)
        list_values = None if not all_results else []
        for e in entities:
            if e["entity"] == entity:
                if not all_results:
                    return e["value"]
                else:
                    list_values.append(e["value"])

        return list_values


class CancelRestarauntTypeSlot(Action):
    """class to reset restaurant_type slot"""

    def name(self) -> Text:
        return "action_reset_restaurant_type"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("restaurant_type", None)]


class CancelReviewSlots(Action):
    """class to reset the star slots"""

    def name(self) -> Text:
        return "action_reset_review"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("stars", None), SlotSet("set_restaurant_list", None)]


class CancelRestaurantName(Action):
    """class to reset restaurant_name slot"""

    def name(self) -> Text:
        return "action_reset_restaurant_name"

    async def run(self, dispatcher: CollectingDispatcher,
                  tracker: Tracker,
                  domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        return [SlotSet("restaurant_name", None)]


class ReadRestaurantList:
    """class to retrieve the last restaurant list"""

    @staticmethod
    def read_list(tracker):
        value = tracker.get_slot("restaurant_list")
        if not value:
            return []
        else:
            return value[0]


class ValidateReviewForm(FormValidationAction):
    """class to check the star slots"""

    def check_star(self, slot_value):
        return slot_value in range(1, 6)

    def name(self) -> Text:
        return "validate_form_review"

    async def extract_stars(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict
    ) -> Dict[Text, Any]:
        star_1 = SearchEntities.return_last_entity(
            tracker, "star_1")

        star_2 = SearchEntities.return_last_entity(
            tracker, "star_2")

        star_1_2 = SearchEntities.return_last_entity(
            tracker, "star_1_2", all_results=True)

        single_star = SearchEntities.return_last_entity(
            tracker, "single_star")

        if (star_1 or star_2) is not None:
            return {"stars": [star_1, star_2]}

        if single_star is not None:
            return {"stars": [single_star, single_star]}

        if star_1_2 is not None:
            if (len(star_1_2) < 2):
                dispatcher.utter_message(
                    text="I think there is a missing star")
            else:
                return {"stars": [star_1_2[0], star_1_2[1]]}

        return {}

    def validate_stars(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:

        if slot_value is not None:
            star_1, star_2 = (int(slot_value[0]) if slot_value[0] != None else None, int(
                slot_value[1]) if slot_value[1] != None else None)
            if (star_1 is not None and not self.check_star(star_1)) or (star_2 is not None and not self.check_star(star_2)):
                dispatcher.utter_message(
                    text="star 1/2 must be between 1 and 5")
                return {"stars": None}

            # if star_1 is not specified, it will take value 0 (ex. "i want maximum 4 stars")
            # if star_2 is not specified, it will take take value 5 (ex. "minimum 2 stars")
            return {"stars": [star_1 or 0, star_2 or 5]}
        else:
            dispatcher.utter_message(text="I need at least one star")
            return {"stars": None}




class SetRestaurantList(Action):
    """class to create the new restaurant list"""

    def name(self):
        return 'action_set_restaurant_list'

    def run(self, dispatcher, tracker, domain):
        df = SingletonReadingCsv.get_csv()

        # if the user says "i don't want stars", they will be [0,5]
        stars = tracker.get_slot("stars") or [0, 5]

        star_1 = stars[0]
        star_2 = stars[1]

        if star_1 > star_2:
            star_1, star_2 = star_2, star_1

        category = tracker.get_slot("restaurant_type")

        dispatcher.utter_message(text="Restaurant category: " + category)
        dispatcher.utter_message(text="Minimum star: " + str(star_1))
        dispatcher.utter_message(text="Maximum star: " + str(star_2))

        dispatcher.utter_message(
 text="-"*10)

        values = (df[(df['average_review'] >= star_1) & (
            df['average_review'] <= star_2) & (df['restaurant_type'].str.lower() == category.lower())])

        if len(values) > 5:
            values = values.sample(n=5)
            
        random_restaurants = dict()

        for _, row in values.iterrows():
            random_restaurants[row["name"]] = [
                "Phone: " + row["phone"], "Website: " + row["website"], "Average review: " + str(round(row["average_review"], 2))]
        if len(values) > 0:
            return [SlotSet("restaurant_list", random_restaurants), SlotSet("set_restaurant_list", True)]

        return [SlotSet("restaurant_list", None),SlotSet("set_restaurant_list", False)]


class GiveRestaurantList(Action):
    """class to display the restaurant list"""

    def name(self):
        return 'action_give_last_restaurant_list'

    def run(self, dispatcher, tracker, domain):

        restaurants = ReadRestaurantList.read_list(tracker)

        if not restaurants:
            dispatcher.utter_message(
                text="no restaurant found")
            return []

        restaurant_names = restaurants.keys()

        dispatcher.utter_message(
            text="I show you the list of the " + str(len(restaurant_names)) + " restaurants found:")

        dispatcher.utter_message(
            text="-"*10)

        for restaurant in restaurant_names:
            dispatcher.utter_message(
                text=restaurant)

        return []


class GiveRestaurantInfo(Action):
    """class to retrieve the info of one of the places inside the last restaurant list"""

    def name(self):
        return 'action_give_restaurant_info'

    def run(self, dispatcher, tracker, domain):

        restaurant_list = ReadRestaurantList.read_list(tracker)

        dispatcher.utter_message(
            text="I give you the restaurant info: ")
        dispatcher.utter_message(
            text="-"*10)

        details = restaurant_list[tracker.get_slot("restaurant_name")]
        for detail in details:
            dispatcher.utter_message(
                text=detail)

        return []


class ActionForget(Action):
    def name(self) -> Text:
        return "action_forget"

    def run(
        self,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any],
    ) -> List[Dict[Text, Any]]:

        # forget last intent
        return [UserUtteranceReverted()]
