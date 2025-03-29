from django.http import JsonResponse
from django.shortcuts import render, redirect
from .models import Medical, User, Ment, Profile
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib import auth
import numpy as np
import os
from django.contrib import messages
import joblib as joblib
from django.contrib.auth.hashers import make_password
from joblib import load


def about(request):
	return render(request, 'about.html')


def doctor_list(request):
	return render(request, 'doctors.html')


def home(request):
	return render(request, 'home.html')


def registerView(request):
	return render(request, 'register.html')


def registerUser(request):
	if request.method == 'POST':
		username = request.POST['username']
		email = request.POST['email']
		password = request.POST['password']
		password = make_password(password)

		a = User(username=username, email=email, password=password, is_patient=True)
		a.save()
		messages.success(request, 'Account Was Created Successfully')
		return redirect('reg')
	else:
		messages.error(request, 'Failed To Register, Try Again Later')
		return redirect('reg')


def loginView(request):
	if request.method == 'POST':
		username = request.POST['username']
		password = request.POST['password']
		user = authenticate(request, username=username, password=password)
		if user is not None and user.is_active:
			auth.login(request, user)
			if user.is_patient:
				return redirect('patient')
			elif user.is_doctor:
				return redirect('doctor')
			else:
				return redirect('login')
		else:
			messages.info(request, "Invalid Username Or Password")
			return redirect('login')
	else:
		return render(request, 'login.html')					



def doctor_home(request):
	doctor = User.objects.filter(is_doctor=True).count()
	patient = User.objects.filter(is_patient=True).count()
	appointment = Ment.objects.filter(approved=True).count()
	medical1 = Medical.objects.filter(medicine='See Doctor').count()
	medical2 = Medical.objects.all().count()
	medical3 = int(medical2) - int(medical1)
	
	context = {'doctor':doctor, 'ment':appointment, 'patient':patient, 'drug':medical3}
	return render(request, 'doctor/home.html', context)



def patient_home(request):
	doctor = User.objects.filter(is_doctor=True).count()
	patient = User.objects.filter(is_patient=True).count()
	appointment = Ment.objects.filter(approved=True).count()
	medical1 = Medical.objects.filter(medicine='See Doctor').count()
	medical2 = Medical.objects.all().count()
	medical3 = int(medical2) - int(medical1)

	user_id = request.user.id
	user_profile = Profile.objects.filter(user_id=user_id)
	if not user_profile:
		context = {'profile_status':'Please Create Profile To Continue', 'doctor':doctor, 'ment':appointment, 'patient':patient, 'drug':medical3}
		return render(request, 'patient/home.html', context)
	else:
		context = {'status':'1', 'doctor':doctor, 'ment':appointment, 'patient':patient, 'drug':medical3}
		return render(request, 'patient/home.html', context)



def create_profile(request):
	if request.method == 'POST':
		birth_date = request.POST['birth_date']
		region = request.POST['region']
		country = request.POST['country']
		gender = request.POST['gender']
		user_id = request.user.id

		Profile.objects.filter(id = user_id).create(user_id=user_id, birth_date=birth_date, gender=gender, region=region)
		messages.success(request, 'Your Profile Was Created Successfully')
		return redirect('patient')
	else:
		user_id = request.user.id
		users = Profile.objects.filter(user_id=user_id)
		users = {'users':users}
		choice = ['1','0']
		gender = ["Male", "Female"]
		context = {"users": {"users":users}, "choice":{"choice":choice}, "gender":gender}
		return render(request, 'patient/create_profile.html', context)	



def diagnosis(request):
	symptoms = ['fever_for_two_weeks','coughing_blood','sputum_mixed_with_blood','night_sweats ','chest_pain','back_pain_in_certain_parts ','shortness_of_breath','weight_loss ','body_feels_tired','lumps_that_appear_around_the_armpits_and_neck','cough_and_phlegm_continuously_for_two_weeks_to_four_weeks','swollen_lymph_nodes','loss_of_appetite','dry_cough','difficulty_in_breathing','sore_throat','pains','nasal_congestion','runny_nose']
	symptoms = sorted(symptoms)
	context = {'symptoms':symptoms, 'status':'1'}
	return render(request, 'patient/diagnosis.html', context)


@csrf_exempt
def MakePredict(request):
	s1 = request.POST.get('s1')
	s2 = request.POST.get('s2')
	s3 = request.POST.get('s3')
	s4 = request.POST.get('s4')
	s5 = request.POST.get('s5')
	id = request.POST.get('id')
	
	list_b = [s1,s2,s3,s4,s5]
	print(list_b)

	list_a = ['fever_for_two_weeks','coughing_blood','sputum_mixed_with_blood','night_sweats ','chest_pain','back_pain_in_certain_parts ','shortness_of_breath','weight_loss ','body_feels_tired','lumps_that_appear_around_the_armpits_and_neck','cough_and_phlegm_continuously_for_two_weeks_to_four_weeks','swollen_lymph_nodes','loss_of_appetite','dry_cough','difficulty_in_breathing','sore_throat','pains','nasal_congestion','runny_nose']

	# Loop to convert all symptoms into 0's
	list_c = [] # Empty list to store disease symptoms converted into 0's and 1's
	for x in range(0,len(list_a)):
		list_c.append(0)

	print(list_c)


	# For all matched specific disease symptoms in general put 1 and unmatched put 0
	for z in range(0,len(list_a)):
		for k in list_b:
			if(k==list_a[z]):
				list_c[z]=1

	test = list_c
	test = np.array(test)
	test = np.array(test).reshape(1,-1)
	print(test.shape)

	clf = joblib.load('model/decision_tree.pkl')

	prediction = clf.predict(test)
	result = prediction[0]

	a = Medical(s1=s1, s2=s2, s3=s3, s4=s4, s5=s5, disease=result, patient_id=id)
	a.save()

	return JsonResponse({'status':result})			



def patient_result(request):
	user_id = request.user.id
	disease = Medical.objects.all().filter(patient_id=user_id)
	context = {'disease':disease, 'status':'1'}
	return render(request, 'patient/result.html', context)


@csrf_exempt
def MakeMent(request):
	disease = request.POST.get('disease')
	userid = request.POST.get('userid')

	try:
		check_medical = Ment.objects.filter(medical_id=disease).exists()
		if(check_medical == False):
			a = Ment(medical_id=disease, patient_id=userid)
			a.save()
			return JsonResponse({'status':'saved'})
		else:
			print('Appointment Exist')
			return JsonResponse({'status':'exist'})
	except Exception as e:
		return JsonResponse({'status':'error'})			


def patient_ment(request):
	user_id = request.user.id
	appointment = Ment.objects.all().filter(patient_id=user_id)
	context = {'ment':appointment, 'status':'1'}
	return render(request, 'patient/ment.html', context)



def logoutView(request):
	logout(request)
	return redirect('login')



def doctor_commend(request):
	user_id = request.user.id
	disease = Medical.objects.all()
	context = {'disease':disease}
	return render(request, 'doctor/result.html', context)



@login_required
@csrf_exempt
def MakeMend(request):
  disease = request.POST.get('disease')
  userid = request.POST.get('userid')

  print('Disease ID',disease)
  print('User ID is',userid)


  patient_id = Medical.objects.filter(pk=disease).values_list('patient_id', flat=True)
  patient_id = list(patient_id)
  patient_id = patient_id[0]
  disease_id = disease


  dob = Profile.objects.filter(user_id=patient_id).values_list('birth_date', flat=True)
  dob = list(dob)
  dob = dob[0]
  print('Date of birth is',dob)
  dob = str(dob)
  dob = dob[0:4]
  print('New Date of birth is',dob)
  dob = int(dob)
  age = 2021 - dob
  print('Patient Age is',age)
  

  gender = Profile.objects.filter(user_id=patient_id).values_list('gender', flat=True)
  gender = list(gender)
  gender = gender[0]
  print('Patient Gender is',gender)

  if gender == 'Male':
      sex = 1
  else:
      sex = 0
  
  print('Patient Sex is',sex)
  
  sick = Medical.objects.filter(pk=disease).values_list('disease', flat=True)
  sick = list(sick)
  sick = sick[0]
  sick = str(sick)

  print('Patient Disease Diagnosed is',sick)
  
  disease_list = ['Acne','Allergy','Diabetes','Fungal infection','Urinary tract infection','Malaria','Malaria','Migraine','Hepatitis B','AIDS']
  
  disease_dict = {'Acne':0,'Allergy':1,'Diabetes':2,'Fungal infection':3,'Urinary tract infection':4,'Malaria':5,'Malaria':6,'Migraine':7,'Hepatitis B':8, 'AIDS':9}

  if sick in disease_list:
      print('AI Got Drug For This Disease')
      print(disease_dict.get(sick))
      new_sick = disease_dict.get(sick)

      test = [new_sick,sex,age]
      print(test)
      test = np.array(test)
      print(test.shape)
      test = np.array(test).reshape(1,-1)
      print(test.shape)
      
      clf = joblib.load('model/medical_rf.pkl')
      prediction = clf.predict(test)
      prediction = prediction[0]
      print('Predicted Disease Is',prediction)

      try:
          check_medical = Medical.objects.filter(patient_id=disease).exists()
          if(check_medical == False):
              Medical.objects.filter(pk= disease).update(medicine=prediction)
              return JsonResponse({'status':'recommended'})
          else:
              print('Drug Exist')
          return JsonResponse({'status':'exist'}) 
      except Exception as e:
          print(e)    
  else:
      print('AI Can Not Recommend Drug')
      Medical.objects.filter(pk= disease).update(medicine='See Doctor')
      return JsonResponse({'status':'not is store'})





@login_required
def doctor_ment(request):
    user_id = request.user.id
    appointment = Ment.objects.all()
    context = {'ment':appointment, 'status':'1'}
    return render(request, 'doctor/ment.html', context)




@login_required
@csrf_exempt
def SaveMent(request):
	pk = request.POST.get('pk')
	day = request.POST.get('day')
	time = request.POST.get('time')


	disease = Ment.objects.filter(pk=pk).exists()
	print(disease)
	user_id = request.user.id



	try:
		check_ment = Ment.objects.filter(pk=pk).exists()
		if(check_ment == True):
			Ment.objects.filter(id=pk).update(approved=True,ment_day=day,time=time,doctor_id=user_id)
			return JsonResponse({'status':'Appointment Set'})
		else:
			print('Appointment Not Exist')
			return JsonResponse({'status':'not exist'}) 
	except Exception as e:
			print(e)
			return JsonResponse({'status':'error'}) 