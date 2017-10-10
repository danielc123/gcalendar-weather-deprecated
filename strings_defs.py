# -*- coding: utf-8 -*-
def gettext( text, lang='en' ):
    weekdays=('Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 
               'Saturday', 'Sunday', 'Today')
    if not (text in weekdays) and lang=='en':
        return text
    else:
        strings={
            'en':{
                'Monday':'MON', 'Tuesday':'TUE', 'Wednesday':'WED', 
                'Thursday':'THU', 'Friday':'FRI', 'Saturday':'SAT', 
                'Sunday':'SUN', 'Today':'TOD'        
            },
            'es':{
                'Monday':'LUN', 'Tuesday':'MAR', 'Wednesday':u'MIÉ', 
                'Thursday':'JUE', 'Friday':'VIE', 'Saturday':u'SÁB', 
                'Sunday':'DOM', 'Today':'HOY',
                'Windchill': u'Sens. térmica', 'Windspeed':'Vel. viento',
                'Direction': u'Direccion', 'Barometer': u'Presión', 'Humidity':'Humedad',
                'Sunrise': 'Salida de sol', 'Sunset': 'Puesta de sol', 'Daylight': 'Horas de sol',
                'Sunset in (Hrs:Min)':'Puesta de sol en (hrs:min)', 'Update':'Actualizado',
                'Sunrise in (Hrs:Min)':'Salida de sol en (hrs:min)', 'Current Cond': u'Condición actual',
                'Outside Temp':'Temperatura exterior', 'Visibility':'Visibilidad', 
                'Showers':'Lluvias',
                'Mostly Cloudy':'Mayormente Nublado', 'Partly Cloudy': 'Parcialmente Nublado', 'Cloudy':'Nublado',
                'Windy':'Ventoso', 'Sunny':'Soleado', 'Fair':'Bueno'
            }
        }
        return strings[lang][text]
    



