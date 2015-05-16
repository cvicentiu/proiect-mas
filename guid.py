class GUID(object):
  guid_counter = 0
  @staticmethod
  def next_guid():
    GUID.guid_counter += 1
    return GUID.guid_counter
