from .._edusys_abc import AbstractHduEduSysModule

BASE_URL = "https://newjw.hdu.edu.cn/jwglxt"
LOGIN_FAIL_FLAG = "/jwglxt/xtgl/login_slogin.html"
API_COURSE_CHOSEN = "/xsxk/zzxkyzb_cxZzxkYzbChoosedDisplay.html"
API_DISPLAY_PAGE = "/xsxk/zzxkyzb_cxZzxkYzbDisplay.html"
API_COURSE_LIST = "/xsxk/zzxkyzb_cxZzxkYzbPartDisplay.html"
API_COURSE_DETAIL = "/xsxk/zzxkyzbjk_cxJxbWithKchZzxkYzb.html"
API_CHOOSE_COURSE = "/xsxk/zzxkyzbjk_xkBcZyZzxkYzb.html"
API_DROP_COURSE = "/jwglxt/xsxk/zzxkyzb_tuikBcZzxkYzb.html"
HOME = "/xtgl/index_initMenu.html"
CLASS_TYPE = 3


class CourseSelect(AbstractHduEduSysModule):
    async def get_course_list(self):
        pass
