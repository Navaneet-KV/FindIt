class LostItem:
    def __init__(self, name, category, location, description, image, holder_id):
        self.name = name
        self.category = category
        self.location = location
        self.description = description
        self.image = image
        self.status = "found"      # consistent with database
        self.holder_id = holder_id
