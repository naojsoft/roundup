import groupperm as gpm


def init(instance):
    instance.registerUtil('getCategory', gpm.getCategory)
    instance.registerUtil('getUserCategories', gpm.getUserCategories)
