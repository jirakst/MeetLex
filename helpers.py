"""
 Inspired by Amazon Lex AWS Blueprint: ScheduleAppointment
 
 PROJECT: MeetLex
 DESCRIPTION: Chatbot-based Virtual Assistant meeting scheduler
 AUTHOR: Stanislav Jirak
 DATE: 10.5.2021
"""

import json
import dateutil.parser
import datetime
import time
import os
import math
import random
import logging

from helpers import eliacit_slot, confirm_intent, close, delegate, build_response_card
from validations import *

logger = logging.getLogger()
logger.setLevel(logging.DEBUG)


""" --- Logic --- """


def schedule_meeting(intent_request):
    """
    Performs dialog management and fulfillment for booking a personal meeting.

    Beyond fulfillment, the implementation for this intent demonstrates the following:
    1) Use of elicitSlot in slot validation and re-prompting
    2) Use of confirmIntent to support the confirmation of inferred slot values, when confirmation is required
    on the bot model and the inferred slot values fully specify the intent.
    """
    
    meeting_person = intent_request['currentIntent']['slots']['Person']
    meeting_type = intent_request['currentIntent']['slots']['MeetingType']
    meeting_date = intent_request['currentIntent']['slots']['Date']
    meeting_time = intent_request['currentIntent']['slots']['Time']
    meeting_duration = intent_request['currentIntent']['slots']['Duration']
    meeting_address = intent_request['currentIntent']['slots']['Address']
    invitation_link = intent_request['currentIntent']['slots']['InvitationLink']
    phone_number = intent_request['currentIntent']['slots']['Phone']
    source = intent_request['invocationSource']
    output_session_attributes = intent_request['sessionAttributes'] if intent_request['sessionAttributes'] is not None else {}
    booking_map = json.loads(try_ex(lambda: output_session_attributes['bookingMap']) or '{}')

    if source == 'DialogCodeHook':
        # Perform basic validation on the supplied input slots.
        slots = intent_request['currentIntent']['slots']
        validation_result = validate_schedule_meeting(meeting_duration, date, meeting_time)
        if not validation_result['isValid']:
            slots[validation_result['violatedSlot']] = None
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                validation_result['violatedSlot'],
                validation_result['message']
            )

        if not meeting_person:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Person',
                {'contentType': 'PlainText', 'content': 'Who is gonna be that with?'}
            )
        
        if meeting_person and not meeting_type:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'MeetingType',
                {'contentType': 'PlainText', 'content': 'What type of meeting would you like to schedule?'}
            )

        if meeting_person and meeting_type and not meeting_date:
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Date',
                {'contentType': 'PlainText', 'content': 'When would you like to schedule your {} ?'.format(meeting_type)}
            )

        if meeting_type and meeting_date:
            # Fetch or generate the availabilities for the given date.
            booking_availabilities = try_ex(lambda: booking_map[meeting_date])
            if booking_availabilities is None:
                booking_availabilities = get_availabilities(meeting_date)
                booking_map[meeting_date] = booking_availabilities
                output_session_attributes['bookingMap'] = json.dumps(booking_map)

            meeting_type_availabilities = get_availabilities_for_duration(get_duration(meeting_type), booking_availabilities)
            if len(meeting_type_availabilities) == 0:
                # No availability on this day at all; ask for a new date and time.
                slots['Date'] = None
                slots['Time'] = None
                return elicit_slot(
                    output_session_attributes,
                    intent_request['currentIntent']['name'],
                    slots,
                    'Date',
                    {'contentType': 'PlainText', 'content': 'There is not any availability on that date, is there another day which works for you?'}
                )

            message_content = 'What time on {} works for you? '.format(meeting_date)
            if meeting_time:
                output_session_attributes['formattedTime'] = build_time_output_string(meeting_time)
                # Validate that proposed time for the meeting can be booked by first fetching the availabilities for the given day.  To
                # give consistent behavior in the sample, this is stored in sessionAttributes after the first lookup.
                if is_available(meeting_time, get_duration(meeting_type), booking_availabilities):
                    return delegate(output_session_attributes, slots)
                message_content = 'The time you requested is not available. '

            if len(meeting_type_availabilities) == 1:
                # If there is only one availability on the given date, try to confirm it.
                slots['Time'] = meeting_type_availabilities[0]
                return confirm_intent(
                    output_session_attributes,
                    intent_request['currentIntent']['name'],
                    slots,
                    {
                        'contentType': 'PlainText',
                        'content': '{}{} is our only availability, does that work for you?'.format
                                   (message_content, build_time_output_string(meeting_type_availabilities[0]))
                    },
                    build_response_card(
                        'Confirm Meeting',
                        'Is {} on {} okay?'.format(build_time_output_string(meeting_type_availabilities[0]), date),
                        [{'text': 'yes', 'value': 'yes'}, {'text': 'no', 'value': 'no'}]
                    )
                )

            available_time_string = build_available_time_string(meeting_type_availabilities)
            return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                slots,
                'Time',
                {'contentType': 'PlainText', 'content': '{}{}'.format(message_content, available_time_string)},
                build_response_card(
                    'Specify Time',
                    'What time works best for you?',
                    build_options('Time', meeting_type, meeting_date, booking_map)
                )
            )
            
            if meeting_type = 'online' and meeting_person and meeting_date and meeting_time and not invitation_link:
               return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'InvitationLink',
                {'contentType': 'PlainText', 'content': 'Can you paste your invitation link in here, please?'}
            )
            
            if (meeting_type = 'personal' or meeting_type = 'inperson') and meeting_person and meeting_date and meeting_time and not meeting_address:
               return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Address',
                {'contentType': 'PlainText', 'content': 'Where the {} will take place?', .format(meeting_type)}
            )
            
            if meeting_person and meeting_type and meeting_date and meeting_time and (invitation_link or meeting_address) and not contact_phone"
                return elicit_slot(
                output_session_attributes,
                intent_request['currentIntent']['name'],
                intent_request['currentIntent']['slots'],
                'Phone',
                {'contentType': 'PlainText', 'content': 'Can you leave your contact phone number here, please?'}

        return delegate(output_session_attributes, slots)
        
        
    """ --- Check avalibility --- """


    # Book the meeting.
    booking_availabilities = booking_map[meeting_date]
    if booking_availabilities:
        # Remove the availability slot for the given date as it has now been booked.
        booking_availabilities.remove(meeting_time)
        if meeting_duration == 60:
            second_half_hour_time = increment_time_by_thirty_mins(meeting_time)
            booking_availabilities.remove(second_half_hour_time)

        booking_map[date] = booking_availabilities
        output_session_attributes['bookingMap'] = json.dumps(booking_map)
    else:
        # This is not treated as an error as this code sample supports functionality either as fulfillment or dialog code hook.
        logger.debug('Availabilities for {} were null at fulfillment time.  '
                     'This should have been initialized if this function was configured as the dialog code hook'.format(meeting_date))

    return close(
        output_session_attributes,
        'Fulfilled',
        {
            'contentType': 'PlainText',
            'content': 'Okay, I have booked your meeting. See you at {} on {}'.format(build_time_output_string(meeting_time), meeting_date)
        }
    )


""" --- Intents --- """


def dispatch(intent_request):
    """
    Called when the user specifies an intent for this bot.
    """

    logger.debug('dispatch userId={}, intentName={}'.format(intent_request['userId'], intent_request['currentIntent']['name']))

    intent_name = intent_request['currentIntent']['name']

    # Dispatch to your bot's intent handlers
    if intent_name == 'ScheduleMeeting':
        return schedule_meeting(intent_request)
    raise Exception('Intent with name ' + intent_name + ' not supported')


""" --- Main handler --- """


def lambda_handler(event, context):
    """
    Route the incoming request based on intent.
    The JSON body of the request is provided in the event slot.
    """
    # By default, treat the user request as coming from the Europe/Paris time zone.
    os.environ['TZ'] = 'Europe/Paris'
    time.tzset()
    logger.debug('event.bot.name={}'.format(event['bot']['name']))

    return dispatch(event)