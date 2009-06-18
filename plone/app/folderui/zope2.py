from DateTime import DateTime

## datetime <--> (ZOPE2) DateTime conversion:
def datetime_to_zopedt(dt):
    if dt is None:
        return None
    return DateTime(dt.isoformat())


def zopedt_to_datetime(zdt):
    if zdt is None:
        return None
    return parseiso(zdt.ISO8601())

