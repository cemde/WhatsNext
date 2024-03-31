INSERT INTO projects (name, description, status) VALUES
	('LLM', 'Improving LLM', 'ACTIVE'),
	('Vision', 'Improving Vision',  'ACTIVE'),
	('AGI', 'Inventing AGI', 'ACTIVE');


INSERT INTO tasks (name, project_id) VALUES
	('Train', 1),
	('Inference', 1),
	('Pre-training', 2),
	('Fine-tuning', 2),
	('Inference', 2);


INSERT INTO jobs (name, project_id, task_id, parameters, status, priority, depends) VALUES
	('speedy-fog-1', 1, 1, '{}', 'PENDING', 0, '{}'),
	('speedy-fog-2', 2, 1, '{}', 'PENDING', 0, '{}'),
	('speedy-fog-3', 1, 2, '{}', 'PENDING', 0, '{}'),
	('speedy-fog-4', 2, 2, '{}', 'PENDING', 0, '{}'),
	('speedy-fog-5', 1, 3, '{}', 'PENDING', 0, '{}'),
	('speedy-fog-6', 1, 4, '{}', 'PENDING', 0, '{}');


SELECT jobs.*, tasks.name FROM jobs JOIN tasks ON jobs.task_id = tasks.id;

