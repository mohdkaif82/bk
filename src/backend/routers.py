from .accounts.viewsets import UserViewSet, PatientLoginViewSet, StaffLoginViewSet,DoctorViewSet,SocialMediaViewSet,userSignupView
from .appointment.viewsets import AppointmentViewSet,OpdViewSet,AssignOpdViewSet
from .base.api.routers import PlutonicRouter
from .billing.viewsets import PatientInvoicesViewSet, PatientPaymentViewSet, PatientsPromoCodeViewSet, \
    PatientWalletViewSet, PatientWalletLedgerViewSet, ReturnPaymentViewSet, PatientProformaInvoicesViewSet
from .blog.viewsets import PostViewSet, VideoFileViewSet, DiseaseViewSet, EventsViewSet, ContactUsViewSet, \
    PageSEOViewSet, SliderViewSet, FacilityViewSet, LandingPageContentViewSet, LandingPageVideoViewSet, CommentViewSet, \
    RatingViewSet, ProductContentViewSet, TherapyContentViewSet, SuggestionBoxViewSet, ConversionViewSet, \
    BlogImageViewSet, ContactUsFormViewSet, DynamicDataViewSet, CareersViewSet
from .inventory.viewsets import ManufacturerViewSet, PracticeInventoryViewSet, InventoryItemViewSet, \
    StockEntryItemViewSet, ItemTypeStockViewSet
from .meeting.viewsets import MeetingViewSet
from .mission_arogyam.viewsets import ArogyamPostViewSet, ArogyamVideoFileViewSet, ArogyamDiseaseViewSet, \
    ArogyamEventsViewSet, ArogyamContactUsViewSet, ArogyamPageSEOViewSet, ArogyamSliderViewSet, ArogyamCommentViewSet, \
    ArogyamRatingViewSet, ArogyamContactUsFormViewSet, ArogyamSuggestionBoxViewSet
from .mlm.viewsets import ProductMarginViewSet, RoleComissionViewSet
from .mlm_compensation.viewsets import PointsToBusinessAdvisorViewSet, ProductMarginAdvisorViewSet, RoleComissionAdvisorViewSet
from .muster_roll.viewsets import HrSettingsViewSet, TasksViewSet
from .patients.viewsets import PatientViewSet,SearchMedicanViewSet,SymptomsViewSet,DiseasesViewSet,patients_video_ViewSet
from .patients.viewsets import PatientViewSet,SearchMedicanViewSet,SymptomsViewSet,DiseasesViewSet,\
    PatientProfileViewSet,ServiceViewSet
from .practice.viewsets import PracticeViewSet, PracticeStaffViewSet, ExpensesViewSet, \
    VendorViewSet, ActivityLogViewSet, PracticeUserPermissionsViewSet, PushNotificationViewSet, NoticeBoardViewSet

from .android_user.viewsets import AppSliderViewSet,AppTestimonialViewSet,AppBlogViewSet,AppBlogCategoryViewSet,AppYoutubeCategoryViewSet,AppYoutubeViewSet

restricted_router = PlutonicRouter()
# Auth App
restricted_router.register(r'users_signup', userSignupView, basename='v1_auth')
#userSignupView pk

restricted_router.register(r'users', UserViewSet, basename='v1_auth')
restricted_router.register(r'patient_login', PatientLoginViewSet, basename='v1_patient_login')
restricted_router.register(r'staff_login', StaffLoginViewSet, basename='v1_staff_login')
restricted_router.register(r'doctor_auth',DoctorViewSet, basename='v1_doctor_view_set')
restricted_router.register(r'socialmedia',SocialMediaViewSet, basename='v1_socialmedia_view_set')


# Practice App
restricted_router.register(r'clinics', PracticeViewSet, basename='v1_practice')
restricted_router.register(r'staff', PracticeStaffViewSet, basename='v1_staff')
restricted_router.register(r'activity', ActivityLogViewSet, basename='v1_activity')
restricted_router.register(r'notification', PushNotificationViewSet, basename='v1_notification')
restricted_router.register(r'noticeboard', NoticeBoardViewSet, basename='v1_NoticeBoardViewSet')

# Patient App

restricted_router.register(r'patients', PatientViewSet, basename='v1_patient')

# patients_video_ViewSet
restricted_router.register(r'patient_testimonials_video', patients_video_ViewSet, basename='pk_patient')

restricted_router.register(r'patientsprofile', PatientProfileViewSet, basename='v1_patientprofile')
restricted_router.register(r'service',ServiceViewSet, basename='v1_service')


#AllopathToAyurvedaViewSet
restricted_router.register(r'searchmedican', SearchMedicanViewSet, basename='v1_searchmedican')
restricted_router.register(r'symptoms', SymptomsViewSet, basename='v1_symptoms')
restricted_router.register(r'diseases', DiseasesViewSet, basename='v1_diseases')


# Billing App
restricted_router.register(r'promocode', PatientsPromoCodeViewSet, basename='v1_promo_code')
restricted_router.register(r'invoice', PatientInvoicesViewSet, basename='v1_invoice')
restricted_router.register(r'payment', PatientPaymentViewSet, basename='v1_payment')
restricted_router.register(r'return', ReturnPaymentViewSet, basename='v1_return')
restricted_router.register(r'proforma', PatientProformaInvoicesViewSet, basename='v1_proforma')
restricted_router.register(r'patient_wallet', PatientWalletViewSet, basename='v1_patient_wallet')
restricted_router.register(r'wallet_ledger', PatientWalletLedgerViewSet, basename='v1_patient_ledger')

# Appointment App
restricted_router.register(r'appointment', AppointmentViewSet, basename='v1_appointment')
restricted_router.register(r'opd', OpdViewSet, basename='v1_opd')
restricted_router.register(r'assign_opd', AssignOpdViewSet, basename='v1_opd')


# BLOG API
restricted_router.register(r'post', PostViewSet, basename='v1_post')
restricted_router.register(r'video', VideoFileViewSet, basename='v1_video')
restricted_router.register(r'disease', DiseaseViewSet, basename='v1_disease')
restricted_router.register(r'events', EventsViewSet, basename='v1_events')
restricted_router.register(r'contactus', ContactUsViewSet, basename='v1_contactus')
restricted_router.register(r'page_seo', PageSEOViewSet, basename='v1_page_seo')
restricted_router.register(r'slider', SliderViewSet, basename='v1_slider')
restricted_router.register(r'facility', FacilityViewSet, basename='v1_facility')
restricted_router.register(r'landing_page_content', LandingPageContentViewSet, basename='v1_landing_page_content')
restricted_router.register(r'landing_page_video', LandingPageVideoViewSet, basename='v1_landing_page_video')
restricted_router.register(r'comment', CommentViewSet, basename='v1_comment')
restricted_router.register(r'rating', RatingViewSet, basename='v1_rating')
restricted_router.register(r'product_content', ProductContentViewSet, basename='v1_product_content')
restricted_router.register(r'therapy_content', TherapyContentViewSet, basename='v1_therapy_content')
restricted_router.register(r'suggestions', SuggestionBoxViewSet, basename='v1_suggestion_box')
restricted_router.register(r'conversion', ConversionViewSet, basename='v1_conversion')
restricted_router.register(r'blogImage', BlogImageViewSet, basename='v1_blog_image')
restricted_router.register(r'contactus-mail', ContactUsFormViewSet, basename='v1_contact_mail')
restricted_router.register(r'dynamic-data', DynamicDataViewSet, basename='v1_dynamic_data')
restricted_router.register(r'apply-online', CareersViewSet, basename='v1_careers')

# MISSION AROGYAM API
restricted_router.register(r'arogyam_post', ArogyamPostViewSet, basename='v1_arogyam_post')
restricted_router.register(r'arogyam_video', ArogyamVideoFileViewSet, basename='v1_arogyam_video')
restricted_router.register(r'arogyam_disease', ArogyamDiseaseViewSet, basename='v1_arogyam_disease')
restricted_router.register(r'arogyam_events', ArogyamEventsViewSet, basename='v1_arogyam_events')
restricted_router.register(r'arogyam_contactus', ArogyamContactUsViewSet, basename='v1_arogyam_contactus')
restricted_router.register(r'arogyam_page_seo', ArogyamPageSEOViewSet, basename='v1_arogyam_page_seo')
restricted_router.register(r'arogyam_slider', ArogyamSliderViewSet, basename='v1_arogyam_slider')
restricted_router.register(r'arogyam_comment', ArogyamCommentViewSet, basename='v1_arogyam_comment')
restricted_router.register(r'arogyam_rating', ArogyamRatingViewSet, basename='v1_arogyam_rating')
restricted_router.register(r'arogyam_suggestions', ArogyamSuggestionBoxViewSet, basename='v1_arogyam_suggestion_box')
restricted_router.register(r'arogyam-contactus-mail', ArogyamContactUsFormViewSet, basename='v1_arogyam_contact_mail')

# Inventory APP
restricted_router.register(r'manufacturer', ManufacturerViewSet, basename='v1_manufacurer')
restricted_router.register(r'inventory', PracticeInventoryViewSet, basename='v1_inventory')
restricted_router.register(r'inventory_item', InventoryItemViewSet, basename='v1_inventory_item')
restricted_router.register(r'item_type_stock', ItemTypeStockViewSet, basename='v1_item_stock')
restricted_router.register(r'stock_entry', StockEntryItemViewSet, basename='v1_stock_entry')
restricted_router.register(r'vendor', VendorViewSet, basename='v1_vendor')
restricted_router.register(r'expenses', ExpensesViewSet, basename='v1_expenses')

# MLM APP
restricted_router.register(r'product_margin', ProductMarginViewSet, basename='v1_product_margin')
restricted_router.register(r'role_commission', RoleComissionViewSet, basename='v1_role_commission')
restricted_router.register(r'user_permissions', PracticeUserPermissionsViewSet, basename='v1_practice_userpermissions')

#MLM_COMPENSATION
restricted_router.register(r'product_margin_advisor',ProductMarginAdvisorViewSet, basename='v1_product_margin_advisor')
restricted_router.register(r'role_commision_advisor',RoleComissionAdvisorViewSet,basename='v1_role_commision_advisor')
restricted_router.register(r'points_to_business',PointsToBusinessAdvisorViewSet,basename='v1_points_to_business_advisor')



# Meeting API
restricted_router.register(r'meetings', MeetingViewSet, basename='v1_meetings')

# HR API
restricted_router.register(r'hr-settings', HrSettingsViewSet, basename='v1_hr_settings')
restricted_router.register(r'tasks', TasksViewSet, basename='v1_tasks')


# Anroid User API
restricted_router.register(r'app-slider', AppSliderViewSet, basename='v1_app_slider')
restricted_router.register(r'app-testimonial', AppTestimonialViewSet, basename='v1_app_testimonial')
restricted_router.register(r'app-blog', AppBlogViewSet, basename='v1_app_blog')
restricted_router.register(r'app-blog-category', AppBlogCategoryViewSet, basename='v1_app_blog_category')
restricted_router.register(r'app-yotube', AppYoutubeViewSet, basename='v1_app_youtube')
restricted_router.register(r'app-yotube-category', AppYoutubeCategoryViewSet, basename='v1_app_youtube_category')


#Doctor app 
# restricted_router.register(r'signup',DoctorViewSet, basename='v1_doctor_view_set')