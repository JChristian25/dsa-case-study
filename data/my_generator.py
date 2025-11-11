import csv, random
from pathlib import Path

out_path = Path('/home/j3yz/Documents/GitHub/dsa-case-study/data/large_input.csv')
num_rows = 15000  # data rows (except sa haeder)

headers = [
    'student_id','last_name','first_name','section',
    'quiz1','quiz2','quiz3','quiz4','quiz5','midterm','final','attendance_percent'
]

first_names = [
    'John','Emily','Michael','Sarah','David','Maria','Carlos','Ana','James','Lisa','Robert','Jennifer',
    'Christopher','Amanda','Daniel','Michelle','Kevin','Jessica','Matthew','Ashley','Joshua','Rachel','Andrew','Nicole',
    'Brandon','Stephanie','Tyler','Megan','Gabriel','Samantha','Alexander','Victoria','Nathan','Brittany','Jordan',
    'Haley','Ryan','Lauren','Connor','Alexis','Ethan','Madison','Jacob','Kaitlyn','Noah','Emma','Caleb','Olivia',
    'Luke','Grace','Mason','Sophia','Austin','Chloe','Hunter','Paige','Hailey','Wyatt','Jasmine','Ian','Mackenzie','Sydney',
    'Garrett','Taylor','Brooke','Jaxon','Morgan','Colton','Avery','Logan','Makayla','Jason','Kayla','Dylan','Alyssa','Justin','Abigail',
    'Brianna','Christian','Evelyn','Jose','Anna','Jonathan','Savannah','Adrian','Vanessa','Oscar','Isabel','Martin','Nora','Samuel','Clara',
    'Leo','Mila','Omar','Priya','Arjun','Mei','Hiro','Yuki','Lucas','Zoe','Finn','Kira','Mateo','Lucia','Hugo','Elena','Amir','Leila','Ibrahim','Sofia'
]

last_names = [
    'Smith','Johnson','Williams','Brown','Jones','Garcia','Martinez','Rodriguez','Wilson','Anderson','Taylor','Thomas',
    'Moore','Jackson','Martin','Lee','Perez','Thompson','White','Harris','Sanchez','Clark','Lewis','Robinson','Walker',
    'Hall','Allen','Young','Hernandez','King','Wright','Lopez','Hill','Scott','Green','Adams','Baker','Gonzalez','Nelson',
    'Carter','Mitchell','Roberts','Turner','Phillips','Campbell','Parker','Evans','Edwards','Collins','Stewart','Morris',
    'Rogers','Reed','Cook','Bailey','Rivera','Cooper','Richardson','Cox','Howard','Ward','Torres','Peterson','Gray','Ramirez',
    'James','Watson','Brooks','Kelly','Sanders','Price','Bennett','Reyes','Long','Foster','Jimenez','Powell','Jenkins','Perry',
    'Hughes','Washington','Flores','Simmons','Patterson','Butler','Bryant','Alexander','Russell','Griffin','Diaz','Hayes','Myers',
    'Ford','Hamilton','Graham','Sullivan','Wallace','Woods','Cole','West','Jordan','Owens','Reynolds','Fisher','Ellis','Hunt','Stone',
    'Nguyen','Patel','Khan','Kim','Singh','Chavez','Mendez','Ramos','Ortiz','Miranda'
]

sections = [
    'BSIT 2-1', 'BSIT 2-2', 'BSIT 2-3', 'BSIT 2-4',
    'BSIT 3-1', 'BSIT 3-2', 'BSIT 3-3',
    'BSIT 1-1', 'BSIT 1-2',
    'BSIT 4-1', 'BSIT 4-2',
    'BSIS 2-1', 'BSIS 2-2'
]

random.seed(42)

def gen_score(min_val=55.0, max_val=100.0):
    # generate scores in 0.5 increments
    val = random.randint(int(min_val*2), int(max_val*2)) / 2.0
    return f"{val:.1f}"

def maybe_blank(value, p_blank=0.04):
    return '' if random.random() < p_blank else value

with out_path.open('w', newline='') as f:
    writer = csv.writer(f)
    writer.writerow(headers)
    for i in range(1, num_rows + 1):
        student_id = f'S{i:03d}' if i < 1000 else f'S{i}'
        first_name = random.choice(first_names)
        last_name = random.choice(last_names)
        section = random.choice(sections)

        quizzes = [maybe_blank(gen_score()) for _ in range(5)]
        midterm = maybe_blank(gen_score())
        final = maybe_blank(gen_score())
        attendance = maybe_blank(gen_score(60.0, 100.0))

        # occasional invalid outlier value to mimic messy real-world data
        if random.random() < 0.0075:  # ~0.75% of rows get one out-of-range value
            idx = random.randrange(8)  # 5 quizzes + midterm + final + attendance
            invalid_val = f"{random.uniform(105.0, 150.0):.1f}"
            if idx < 5:
                quizzes[idx] = invalid_val
            elif idx == 5:
                midterm = invalid_val
            elif idx == 6:
                final = invalid_val
            else:
                attendance = invalid_val

        writer.writerow([
            student_id,
            last_name,
            first_name,
            section,
            *quizzes,
            midterm,
            final,
            attendance,
        ])

print('Wrote file:', out_path)