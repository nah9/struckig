from copy import copy
from pathlib import Path
from sys import path
from dataclasses import dataclass
from typing import List
import uuid
import jinja2
import random
import itertools

@dataclass
class Test:
    
    name: str
    guid: str
    profile_count : int   
    max_velocity: List[str]
    max_acceleration: List[str]
    max_jerk: List[str]     
    current_position: List[str]
    current_velocity: List[str]
    current_acceleration: List[str]          
    target_position: List[str]
    target_velocity: List[str]
    target_acceleration: List[str]
    
    duration: str
    min: List[str]
    max: List[str]
    t_min: List[str]
    t_max: List[str]    

tmpl = jinja2.Template("""
<?xml version="1.0" encoding="utf-8"?>
<TcPlcObject Version="1.1.0.1" ProductVersion="3.1.4024.9">
  <POU Name="GeneratedTest" Id="{8a002d40-1b8b-4a36-917f-04dd149a7db3}" SpecialFunc="None">
    <Declaration><![CDATA[FUNCTION_BLOCK GeneratedTest EXTENDS TcUnit.FB_TestSuite]]></Declaration>
    <Implementation>
      <ST><![CDATA[
{%- for m in methods -%}
{{m.name}}();
{% endfor -%}
]]></ST>
    </Implementation>
{% for m in methods %}
    <Method Name="{{m.name}}" Id="{%raw%}{{%endraw%}{{m.guid}}{%raw%}}{%endraw%}">
      <Declaration><![CDATA[METHOD {{m.name}}
VAR_INST
  ruckig : Struckig.Ruckig(0.001);
  input : Struckig.InputParameter({{m.profile_count}}) := (
    Synchronization := SynchronizationType.TimeSync,        
    MaxVelocity := [ {{ m.max_velocity }} ],
    MaxAcceleration := [ {{ m.max_acceleration }} ],
    MaxJerk := [ {{ m.max_jerk }} ],
    CurrentPosition := [ {{ m.current_position }} ],
    CurrentVelocity := [ {{ m.current_velocity }} ],
    CurrentAcceleration := [ {{ m.current_acceleration }} ],
    TargetPosition := [ {{ m.target_position }} ],
    TargetVelocity := [ {{ m.target_velocity }} ],
    TargetAcceleration := [ {{ m.target_acceleration }} ]
  );
  output : Struckig.OutputParameter;
  positionExtrema : Struckig.PositionExtremaDesc;
END_VAR]]></Declaration>
      <Implementation>
        <ST><![CDATA[TEST('{{ m.name.replace('Test_', '') }}');

ruckig.update(input, output);

// Check total duration of profiles
AssertEquals_LREAL(Expected := {{ m.duration }}, Actual := output.Trajectory.Duration, DELTA := 1E-8, Message := 'Duration incorrect');

// Check duration for each phase
{%- for i in range(m.profile_count) %}
positionExtrema := output.trajectory.profiles[{{i}}].positionExtrema();
AssertEquals_LREAL({{ m.t_max[i] }}, positionExtrema.Tmax, 1E-9, message:='Profile[{{i}}] Tmax incorrect');
AssertEquals_LREAL({{ m.max[i] }}, positionExtrema.Maximum, 1E-9, message:='Profile[{{i}}] maximum incorrect');
AssertEquals_LREAL({{ m.t_min[i] }}, positionExtrema.Tmin, 1E-9, message:='Profile[{{i}}] Tmin incorrect');
AssertEquals_LREAL({{ m.min[i] }}, positionExtrema.Minimum, 1E-9, message:='Profile[{{i}}] minimum incorrect');
{% endfor %}   

TEST_FINISHED();]]></ST>
      </Implementation>
    </Method>
{% endfor %}    
  </POU>
</TcPlcObject>
""")

from ruckig import InputParameter, OutputParameter, Result, Ruckig
#import sys
#    
#otg = Ruckig(3, 0.001)
#inp = InputParameter(3)
#inp.current_position = [ 14.0885808545, -33.9152203952, 70.8304765594 ]
#inp.current_velocity = [ 94.9432603820, -555.1227229095, -441.9205790714 ]
#inp.current_acceleration = [ 5028.6398970234, 4367.9597618504, 6063.8211734920 ]
#inp.target_position = [ -18.1406321446, -21.9844574895, 8.5010665680 ]
#inp.target_velocity = [ 711.7005183980, -389.8180727062, -335.3533430373 ]
#inp.target_acceleration = [ 0.0000000000, 0.0000000000, 0.0000000000 ]
#inp.max_velocity = [2000, 2000, 2000]
#inp.max_acceleration = [20000, 20000, 20000]
#inp.max_jerk = [800000, 800000, 800000]
#out = OutputParameter(3)
#
# runtime errors and other errors
#res = otg.update(inp, out)
#            
#sys.exit(-1)

if __name__ == '__main__':
    random_uniform_tuple = lambda x: (random.uniform(-x, x), random.uniform(-x, x), random.uniform(-x, x))
    fmt = lambda x: '{:0.20f}'.format(x)
    
    tests = list()
    i = 0
    count = 0
    while i < 70:
        print(f"Trajectory {i}/{count}")
        count+=1
        target_velocity = random.choice([(0,0,0), random_uniform_tuple(1000) ])
        target_acceleration = random.choice([(0,0,0), random_uniform_tuple(1000) ])
        
        try:
            del(otg)
            del(inp)
            del(out)
        except:
            pass
        
        otg = Ruckig(3, 0.001)
        inp = InputParameter(3)
        inp.current_position = random_uniform_tuple(100)
        inp.current_velocity = random_uniform_tuple(1000)
        inp.current_acceleration = random_uniform_tuple(10000)
        inp.target_position = random_uniform_tuple(100)
        inp.target_velocity = target_velocity
        inp.target_acceleration = target_acceleration
        inp.max_velocity = [2000, 2000, 2000]
        inp.max_acceleration = [20000, 20000, 20000]
        inp.max_jerk = [800000, 800000, 800000]
        out = OutputParameter(3)
        
        # runtime errors and other errors
        try:
            res = otg.update(inp, out)
            if res != Result.Working:
              print('invalid state')
              continue
        except RuntimeError as e:
            print(e)
            continue
        
        i += 1
        target_velocity_suffix = '_HasTargetVelocity' if target_velocity != (0,0,0) else ''
        target_acceleration_suffix = '_HasTargetAcceleration' if target_acceleration != (0,0,0) else ''
    
        t = Test(name=f'Test_Trajectory{target_velocity_suffix}{target_acceleration_suffix}_{i}', 
            guid=str(uuid.uuid4()),
            profile_count=3,
            current_position=', '.join(map(fmt, inp.current_position)),\
            current_velocity=', '.join(map(fmt, inp.current_velocity)),\
            current_acceleration=', '.join(map(fmt, inp.current_acceleration)),\
            target_position=', '.join(map(fmt, inp.target_position)),\
            target_velocity=', '.join(map(fmt, inp.target_velocity)),\
            target_acceleration=', '.join(map(fmt, inp.target_acceleration)),\
            max_velocity=', '.join(map(fmt, inp.max_velocity)),\
            max_acceleration=', '.join(map(fmt, inp.max_acceleration)),\
            max_jerk=', '.join(map(fmt, inp.max_jerk)),\
            duration=fmt(out.trajectory.duration),\
            max=list(map(fmt, [x.max for x in out.trajectory.position_extrema])),\
            min=list(map(fmt, [x.min for x in out.trajectory.position_extrema])),\
            t_min=list(map(fmt, [x.t_min for x in out.trajectory.position_extrema])),\
            t_max=list(map(fmt, [x.t_max for x in out.trajectory.position_extrema]))
        )
              
        print(t)
        tests.append(t)

    print("re-run")
    for t in tests:

        # second run
        otg = Ruckig(3, 0.001)
        inp = InputParameter(3)
        inp.current_position = list(map(float, t.current_position.split(', ')))
        inp.current_velocity = list(map(float, t.current_velocity.split(', ')))
        inp.current_acceleration = list(map(float, t.current_acceleration.split(', ')))
        inp.target_position = list(map(float, t.target_position.split(', ')))
        inp.target_velocity = list(map(float, t.target_velocity.split(', ')))
        inp.target_acceleration = list(map(float, t.target_acceleration.split(', ')))
        inp.max_velocity = [2000, 2000, 2000]
        inp.max_acceleration = [20000, 20000, 20000]
        inp.max_jerk = [800000, 800000, 800000]
        out = OutputParameter(3)
        
        print(t)
        
    with open('Struckig_unittest/struckig_unittest/POUs/GeneratedTest.TcPOU', 'w') as f:
        f.write(tmpl.render(methods=tests).strip())