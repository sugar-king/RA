#include <GL/freeglut.h>
#include <assimp/Importer.hpp>
#include <assimp/postprocess.h>
#include <assimp/scene.h>

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <iostream>
#include <vector>


int numV, numF, numB, numS;

class Face {
public:
	aiVector3D* v1, * v2, * v3;
	Face(aiVector3D vX, aiVector3D vY, aiVector3D vZ) {
		v1 = new aiVector3D(vX); v2 = new aiVector3D(vY); v3 = new aiVector3D(vZ);
	}
};

std::vector<Face*> polygones;
std::vector<aiVector3D*> vertices;
aiVector3D* control_points;
std::vector<aiVector3D> curve_points;
std::vector<aiVector3D> tangents, all_tangents;
aiVector3D center(0.0, 0.0, 0.0);
aiVector3D axes(0.0, 0.0, 0.0);
aiVector3D s(1.0, 0.0, 0.0);
aiVector3D e(0.0, 0.0, 0.0);
float pi = 3.14159265;

GLuint window;
GLuint sub_width = 512, sub_height = 512;

void display();
void idle();
void reshape(int width, int height);

int main(int argc, char** argv)
{
	Assimp::Importer Importer;
	const aiScene* body = new aiScene(*Importer.ReadFile("teddy.obj", 0));
	if (body->mNumMeshes != 1) {

		std::cout << "Invalid shape: " << body->mNumMeshes << std::endl;

		return 0;
	}
	numV = body->mMeshes[0]->mNumVertices;
	numF = body->mMeshes[0]->mNumFaces;
	auto body_vertices = body->mMeshes[0]->mVertices;
	vertices.resize(numV);
	for (int i = 0;i < numV; i++) {
		vertices[i] = new aiVector3D(body_vertices[i].x, body_vertices[i].y, body_vertices[i].z);
	}

	polygones.resize(numF);
	auto body_faces = body->mMeshes[0]->mFaces;
	for (int i = 0;i < numF; i++) {
		polygones[i] = new Face(body_vertices[body_faces[i].mIndices[0]],
								body_vertices[body_faces[i].mIndices[1]],
								body_vertices[body_faces[i].mIndices[2]]);
	}

	const aiScene* trajectory = Importer.ReadFile("trajectory.obj", 0);

	if (trajectory->mNumMeshes != 1) {

		std::cout << "Invalid trajectory: " << trajectory->mNumMeshes << std::endl;

		return 0;
	}

	numB = trajectory->mMeshes[0]->mNumVertices;
	numS = numB - 3;


	control_points = trajectory->mMeshes[0]->mVertices;


	for (int i = 0; i < numV; i++) {
		center.x += vertices[i]->x *numF; center.y += vertices[i]->y * numF; center.z += vertices[i]->z * numF;
	}
	center.x /= numV; center.y /= numV; center.z /= numV;


	curve_points.resize(100 * numS);
	tangents.resize(numS * 8);
	all_tangents.resize(numS * 2 * 100);
	int numT = 0, numAT = 0;

	for (int i = 0; i < numS; i++) {
		aiVector3D v0 = control_points[i];
		aiVector3D v1 = control_points[i + 1];
		aiVector3D v2 = control_points[i + 2];
		aiVector3D v3 = control_points[i + 3];

		for (int t_percent = 0; t_percent < 100; t_percent++) {
			double t = t_percent / 100.0;
			float f1 = (-pow(t, 3.0) + 3 * pow(t, 2.0) - 3 * t + 1) / 6.0;
			float f2 = (3 * pow(t, 3.0) - 6 * pow(t, 2.0) + 4) / 6.0;
			float f3 = (-3 * pow(t, 3.0) + 3 * pow(t, 2.0) + 3 * t + 1) / 6.0;
			float f4 = pow(t, 3.0) / 6.0;


			curve_points[100 * i + t_percent].x = f1 * v0.x + f2 * v1.x + f3 * v2.x + f4 * v3.x;
			curve_points[100 * i + t_percent].y = f1 * v0.y + f2 * v1.y + f3 * v2.y + f4 * v3.y;
			curve_points[100 * i + t_percent].z = f1 * v0.z + f2 * v1.z + f3 * v2.z + f4 * v3.z;

			all_tangents[numAT].x = curve_points[100 * i + t_percent].x;
			all_tangents[numAT].y = curve_points[100 * i + t_percent].y;
			all_tangents[numAT].z = curve_points[100 * i + t_percent].z;
			numAT++;

			float t1 = 0.5 * (-pow(t, 2.0) + 2 * t - 1);
			float t2 = 0.5 * (3 * pow(t, 2.0) - 4 * t);
			float t3 = 0.5 * (-3 * pow(t, 2.0) + 2 * t + 1);
			float t4 = 0.5 * (pow(t, 2.0));

			float vx = t1 * v0.x + t2 * v1.x + t3 * v2.x + t4 * v3.x;
			float vy = t1 * v0.y + t2 * v1.y + t3 * v2.y + t4 * v3.y;
			float vz = t1 * v0.z + t2 * v1.z + t3 * v2.z + t4 * v3.z;

			int scaler = 3;
			all_tangents[numAT].x = all_tangents[numAT - 1].x + vx / scaler;
			all_tangents[numAT].y = all_tangents[numAT - 1].y + vy / scaler;
			all_tangents[numAT].z = all_tangents[numAT - 1].z + vz / scaler;
			numAT++;

			if (t_percent % 50 == 0) {
				tangents[numT].x = curve_points[100 * i + t_percent].x;
				tangents[numT].y = curve_points[100 * i + t_percent].y;
				tangents[numT].z = curve_points[100 * i + t_percent].z;
				numT++;

				tangents[numT].x = all_tangents[numAT - 1].x;
				tangents[numT].y = all_tangents[numAT - 1].y;
				tangents[numT].z = all_tangents[numAT - 1].z;
				numT++;
			}
		}

	}

	glutInitDisplayMode(GLUT_SINGLE | GLUT_RGB);
	glutInitWindowSize(sub_width, sub_height);
	glutInitWindowPosition(100, 100);
	glutInit(&argc, argv);

	window = glutCreateWindow("RA - 1. labos");
	glutReshapeFunc(reshape);
	glutDisplayFunc(display);
	glutIdleFunc(idle);

	glutMainLoop();
	return 0;
}

void reshape(int width, int height)
{
	sub_width = width;
	sub_height = height;

	glViewport(0, 0, sub_width, sub_height);


	glMatrixMode(GL_PROJECTION);
	glLoadIdentity();


	gluPerspective(45.0f, (GLfloat)width / (GLfloat)height, 0.1f, 100.0f);

	glMatrixMode(GL_MODELVIEW);
	glLoadIdentity();

	glClearColor(1.0f, 1.0f, 1.0f, 0.0f);
	glClear(GL_COLOR_BUFFER_BIT);
	glPointSize(1.0);
	glColor3f(0.0f, 0.0f, 0.0f);
}

int t = 0;

void display()
{
	glLoadIdentity();
	glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT);
	glTranslatef(-5.0, -5.0, -75.0);

	bool connect_control_points = false;
	if (connect_control_points) {
		glBegin(GL_LINE_STRIP);
		for (int i = 0; i < numB; i++) {
			glVertex3f(control_points[i].x, control_points[i].y, control_points[i].z);
		}
		glEnd();
	}

	glBegin(GL_LINE_STRIP);
	for (int i = 0; i < 100 * numS; i++) {
		glVertex3f(curve_points[i].x, curve_points[i].y, curve_points[i].z);
	}
	glEnd();


	glBegin(GL_LINES);
	for (int i = 0; i < numS * 8; i += 2) {
		glVertex3f(tangents[i].x, tangents[i].y, tangents[i].z);
		glVertex3f(tangents[i + 1].x, tangents[i + 1].y, tangents[i + 1].z);
	}
	glEnd();

	glTranslatef(curve_points[t].x, curve_points[t].y, curve_points[t].z);

	e.x = all_tangents[2 * t + 1].x - all_tangents[2 * t].x;
	e.y = all_tangents[2 * t + 1].y - all_tangents[2 * t].y;
	e.z = all_tangents[2 * t + 1].z - all_tangents[2 * t].z;

	axes.x = s.y * e.z - e.y * s.z;
	axes.y = e.x * s.z - s.x * e.z;
	axes.z = s.x * e.y - s.y * e.x;

	double absS = pow(pow((double)s.x, 2.0) + pow((double)s.y, 2.0) + pow((double)s.z, 2.0), 0.5);
	double absE = pow(pow((double)e.x, 2.0) + pow((double)e.y, 2.0) + pow((double)e.z, 2.0), 0.5);
	double se = s.x * e.x + s.y * e.y + s.z * e.z;
	double angle = acos(se / (absS * absE));
	angle = angle / (2 * pi) * 360;
	glRotatef(angle, axes.x, axes.y, axes.z);

	glTranslatef(-center.x, -center.y, -center.z);


	glColor3f(1.0, 0.2, 0.2);

	for (int i = 0; i < numF; i++) {
		aiVector3D* v1 = polygones[i]->v1;
		aiVector3D* v2 = polygones[i]->v2;
		aiVector3D* v3 = polygones[i]->v3;

		glBegin(GL_TRIANGLES);
		glVertex3f(center.x + v1->x / 2, center.y + v1->y / 2, center.z + v1->z / 2);
		glVertex3f(center.x + v2->x / 2, center.y + v2->y / 2, center.z + v2->z / 2);
		glVertex3f(center.x + v3->x / 2, center.y + v3->y / 2, center.z + v3->z / 2);
		glEnd();
	}


	glBegin(GL_LINES);

	glColor3f(1.0, 0.0, 0.0);
	glVertex3f(center.x, center.y, center.z);
	glVertex3f(center.x + 2.5, center.y, center.z);

	glColor3f(0.0, 1.0, 0.0);
	glVertex3f(center.x, center.y, center.z);
	glVertex3f(center.x, center.y + 2.5, center.z);

	glColor3f(0.0, 0.0, 1.0);
	glVertex3f(center.x, center.y, center.z);
	glVertex3f(center.x, center.y, center.z + 2.5);

	glColor3f(0.0, 0.0, 0.0);
	glEnd();

	t++;
	if (t == 100 * numS) t = 0;

	glFlush();
}

int currentTime = 0; int previousTime = 0;

void idle() {
	currentTime = glutGet(GLUT_ELAPSED_TIME);
	int timeInterval = currentTime - previousTime;

	if (timeInterval > 10) {
		display();
		previousTime = currentTime;
	}
}