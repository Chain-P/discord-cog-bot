class Birthday:

    def is_birthday(self, birthdays, current_time):
        is_today = False
        for key in birthdays.keys():
            birthday = birthdays[key]
            if (birthday[:-5] == current_time):
                is_today = True
                return is_today, key
        return is_today

    def get_age(self, birthdays, current_time):
        for day in birthdays:
            if (day[-5:] == current_time[-5:]):
                day = day[-5:]
                currrent_time = current_time[-5:]

                print(f"{day} - {currrent_time}")
