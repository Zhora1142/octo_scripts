class Config:
    api_token: str

    profiles: list
    first_profile: int
    profiles_number: int

    metamask_file: str

    thread_number: int

    tag_name: str

    metamask_password: str

    do_metamask: int
    do_keplr: int
    do_phantom: int
    do_backpack: int
    do_sui: int

    def __init__(self, api_token, profiles, first_profile, profiles_number, metamask_file, thread_number, tag_name, metamask_password, do_metamask, do_keplr, do_phantom, do_backpack, do_sui):
        self.api_token = api_token
        self.profiles = list(map(lambda t: int(t), profiles.split(', '))) if profiles else []
        self.first_profile = int(first_profile)
        self.profiles_number = int(profiles_number)
        self.metamask_file = metamask_file
        self.thread_number = int(thread_number)
        self.tag_name = tag_name
        self.metamask_password = metamask_password
        self.do_metamask = int(do_metamask)
        self.do_keplr = int(do_keplr)
        self.do_phantom = int(do_phantom)
        self.do_backpack = int(do_backpack)
        self.do_sui = int(do_sui)
