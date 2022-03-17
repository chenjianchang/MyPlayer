
def change_position_into_time(position):
    return (str(int(int(int(position // 1000) // 60) // 60)).zfill(2)
            + ":" + str(int(int(position // 1000) // 60) - int(int(int(position // 1000) // 60) // 60) * 60).zfill(2)
            + ":" + str(int(position // 1000) - int(int(position // 1000) // 60) * 60 - int(int(int(position // 1000) // 60) // 60) * 3600).zfill(2)
            + "." + str(int(position % 1000)).zfill(3))



def change_time_into_position(time):
    """ time is a string format like 00:01:03.600, return it with a millisecond unit value """
    try:
        return int(time[0:2]) * 60 * 60 * 1000 + int(time[3:5]) * 60 * 1000 + int(time[6:8]) * 1000 + int(time[9:12])
    except:
        print(time + "   this row has some format problems in the subtitle file!")


def get_subtitle(position, subtitle_data):
        subtitle_content = ""
        write_or_not = False
        try:
            for each_line in subtitle_data:
                if "-->" in each_line:
                    if write_or_not:
                        break
                else:
                    if write_or_not:
                        subtitle_content = subtitle_content + each_line
                    continue
                try:
                    if (int(position) >= int(each_line[0:2]) * 60 * 60 * 1000 + int(each_line[3:5]) * 60 * 1000 + int(each_line[6:8]) * 1000 + int(each_line[9:12])
                        or int(position) == int(each_line[0:2]) * 60 * 60 * 1000 + int(each_line[3:5]) * 60 * 1000 + int(each_line[6:8]) * 1000 + int(each_line[9:12])) \
                            and int(position) < int(each_line[17:19]) * 60 * 60 * 1000 + int(each_line[20:22]) * 60 * 1000 + int(each_line[23:25]) * 1000 + int(each_line[26:29]):
                        write_or_not = True
                        continue
                    else:
                        continue
                except:
                    pass
        except:
            subtitle_content = "the subtitle fails"
        return subtitle_content

if __name__ == "__main__":
    pass
